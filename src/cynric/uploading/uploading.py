from datetime import datetime
from io import BytesIO

from pandas import DataFrame  # type: ignore
from valediction.datasets.datasets import Dataset  # type: ignore
from valediction.progress import Progress  # type: ignore
from valediction.support import calculate_runtime, list_as_bullets  # type: ignore

from cynric.api.queue import BCPlatformsQueue
from cynric.credentials.resolution import resolve_credentials
from cynric.exceptions import (
    EmptyDatasetError,
    UnvalidatedDatasetError,
)
from cynric.uploading.helpers import check_target_table_map, _estimate_chunks
from cynric.validation.validation import validate


class Uploader:
    """Upload a Dataset to the Wessex SDE as CSV chunks.

    This class takes a Valediction :class:`Dataset` and accompanying source-to-target table map,
    splits each table into chunks, converts them to CSV in memory, and uploads them to the
    tables via the configured Wessex SDE endpoint. A `base_url` and `token` can be provided, or
    will otherwise be fetched from the OS credential storage, if previously saved with
    `cynric.save_credentials()`.

    Args:
        dataset (Dataset): The Dataset to upload.
        target_table_map (dict[str, str]): Mapping from dataset table names
            (``Dataset`` item names) to Wessex SDE API target dataset table
            identifiers. All Dataset and target table names must match.
        token (str, optional): Authentication token for the Wessex SDE API.
            If not provided, will be fetched from the OS credential storage
            if previously saved.
        base_url (str, optional): Base URL for the Wessex SDE API.
            If not provided, will be fetched from the OS credential storage
            if previously saved.

    Raises:
        TypeError: If ``dataset`` is not a Valediction :class:`Dataset` or
            if ``target_table_map`` is not a dictionary.
        EmptyDatasetError: If the dataset contains no tables.
        ValueError: If the ``target_table_map`` does not match the ``dataset``.
        UnvalidatedDatasetError: If an attempt is made to upload an
            unvalidated dataset, or a dataset validated with issues.
        CredentialNotSaved: If ``token`` or ``base_url`` are not provided and
            have not been saved to the OS credential storage.
    """

    def __init__(
        self,
        dataset: Dataset,
        target_table_map: dict[str, str],
        token: str = "",
        base_url: str = "",
    ):
        self.dataset: Dataset = dataset
        self.target_table_map: dict[str, str] = target_table_map
        self.token: str = token
        self.base_url: str = base_url

        self.__check_dataset()
        self.__check_target_table_map()
        self.__check_credentials()

    # Checks
    def __check_credentials(self) -> None:
        """Checks credentials are valid if provided, or fetches from OS credential
        storage."""
        self.base_url, self.token = resolve_credentials(
            token=self.token, base_url=self.base_url
        )

        self.api: BCPlatformsQueue = BCPlatformsQueue(
            token=self.token, base_url=self.base_url
        )

    def __check_dataset(self) -> None:
        """Ensures that the dataset is a Valediction Dataset."""
        if not isinstance(self.dataset, Dataset):
            raise TypeError("dataset must be a Valediction Dataset")

        if len(self.dataset) == 0:
            raise EmptyDatasetError("Dataset is empty")

    def __check_target_table_map(self) -> None:
        """Ensures that the target table map matches the dataset."""
        check_target_table_map(self.dataset, self.target_table_map)

    def __get_target_table(self, dataset_name: str) -> str:
        """Returns the target table for a given dataset item name."""
        return self.target_table_map[dataset_name]

    # Helpers
    def _create_csv_in_memory(self, df: DataFrame) -> BytesIO:
        """Converts a DataFrame to a CSV in memory."""
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        buffer = BytesIO(csv_bytes)
        buffer.seek(0)
        return buffer

    def _upload_csv_chunk(self, target_table: str, csv_fileobj: BytesIO, filename: str):
        """Uploads a CSV chunk to a target table."""
        self.api.upload_csv_and_wait(
            dataset_id=target_table, source=csv_fileobj, filename=filename
        )

    # Uploading
    def upload(
        self,
        chunk_size: int | None = 10_000_000,
        feedback: bool = True,
        import_data_first: bool = False,
    ) -> None:
        """Upload all tables in the dataset to the Wessex SDE in chunks, according to
        the attached target table map..

        Each table in the dataset is iterated over in chunks, converted to CSV
        in memory, and uploaded to the corresponding target table defined in
        ``target_table_map``. A progress bar is displayed if ``feedback`` is
        enabled.

        Args:
            chunk_size (int | None, optional): Maximum size of each data chunk
                in rows. This also makes use of Valediction's chunk importing,
                if data are not already imported. Defaults to ``10_000_000``.
            feedback (bool, optional): Whether to print and display progress
                information during the upload. Defaults to ``True``.
            import_data_first (bool, optional): If True, imports all data into
                the dataset from disk before uploading (if not yet imported).
                Defaults to ``False``, allowing ``chunk_size`` to propagate
                to Valediction.

        Raises:
            UnvalidatedDatasetError: If any items within the dataset are
                unvalidated of have validation issues.
            Exception: Any error arising from chunk iteration, CSV conversion,
                or the underlying API calls will propagate.
        """
        # Checks
        self.__check_target_table_map()

        if not self.dataset.validated:
            unvalidated_items = [
                item.name for item in self.dataset if not item.validated
            ]
            raise UnvalidatedDatasetError(
                f"Dataset must be validated before uploading. Unvalidated dataset items: {list_as_bullets(unvalidated_items)}"
            )

        if import_data_first:
            self.dataset.import_data()

        if feedback:
            print(f"Uploading {len(self.dataset)} tables")

        steps = 3
        max_name_len = max(len(item.name) for item in self.dataset)

        # Loop over dataset items
        for item in self.dataset:
            start = datetime.now()
            progress = Progress(
                desc=f"Uploading {item.name}:  "
                + " " * (max_name_len - len(item.name)),
                enabled=feedback,
            )
            iterator = item.iterate_data_chunks(chunk_size=chunk_size)
            more_chunks = True

            # Loop over chunks
            while more_chunks:
                try:
                    # Import Chunk
                    progress.begin_step("Importing")
                    chunk = next(iterator)
                    total_chunks = _estimate_chunks(item, chunk, chunk_size)
                    progress.retarget_total(total_chunks * steps)
                    progress.complete_step()

                    # Convert to CSV
                    df = chunk.df
                    progress.begin_step("Converting")
                    csv = self._create_csv_in_memory(df)
                    progress.complete_step()

                    # Upload
                    progress.begin_step("Uploading")
                    target_table = self.__get_target_table(item.name)
                    self._upload_csv_chunk(
                        target_table=target_table,
                        csv_fileobj=csv,
                        filename=f"{item.name}.csv",
                    )
                    progress.complete_step()

                # No more chunks
                except StopIteration:
                    more_chunks = False
                    progress.finish(
                        postfix=f"Completed ({calculate_runtime(start=start).message})",
                        good=True,
                    )
                    progress.close()
                    continue

    def validate_and_upload(
        self,
        chunk_size: int = 10_000_000,
        feedback: bool = True,
        import_data_first: bool = False,
    ) -> None:
        """Upload all tables in the dataset to the Wessex SDE in chunks, according to
        the attached target table map..

        Each table in the dataset is iterated over in chunks, converted to CSV
        in memory, and uploaded to the corresponding target table defined in
        ``target_table_map``. A progress bar is displayed if ``feedback`` is
        enabled.

        Args:
            chunk_size (int | None, optional): Maximum size of each data chunk
                in rows. This also makes use of Valediction's chunk importing,
                if data are not already imported. Defaults to ``10_000_000``.
            feedback (bool, optional): Whether to print and display progress
                information during the upload. Defaults to ``True``.
            import_data_first (bool, optional): If True, imports all data into
                the dataset from disk before uploading (if not yet imported).
                Defaults to ``False``, allowing ``chunk_size`` to propagate
                to Valediction.

        Raises:
            DataIntegrityError: Raised from Valediction if there are data
                integrity issues.
            Exception: Any error arising from chunk iteration, CSV conversion,
                or the underlying API calls will propagate.
        """
        self.__check_target_table_map()

        self.dataset = validate(
            dataset=self.dataset,
            dictionary=self.dataset.dictionary,
            chunk_size=chunk_size,
            feedback=feedback,
            import_data=import_data_first,
        )
        self.dataset.check()  # raises error if validation issues

        self.upload(chunk_size=chunk_size, feedback=feedback)
