from pathlib import Path

import valediction as vale  # type: ignore
from pandas import DataFrame  # type: ignore
from valediction.datasets.datasets import Dataset  # type: ignore
from valediction.dictionary.model import Dictionary  # type: ignore

from cynric.exceptions import NoDictionaryError
from cynric.uploading.uploading import Uploader  # type: ignore


def validate_and_upload(
    dataset: Dataset | str | Path | dict[str, DataFrame],
    target_table_map: dict[str, str],
    chunk_size: int = 10_000_000,
    feedback: bool = True,
    import_data_first: bool = False,
    dictionary: Dictionary | str | Path | None = None,
    token: str = "",
    base_url: str = "",
) -> Dataset:
    """Create or reuse a Dataset, validate it, and upload all tables to the Wessex SDE
    in chunks.

    Takes a Valediction-compatible Dataset and Dictionary, filepaths to the same,
    or a dictionary of DataFrames - alongside a target table map that maps Dataset
    table names to target table names. Validates data, and uploads all data to the
    Wessex SDE in chunks.

    Each table in the dataset is iterated over in chunks, converted to CSV
    in memory, and uploaded to the corresponding target table defined in
    ``target_table_map``. A progress bar is displayed if ``feedback`` is
    enabled.

    A Wessex SDE ``token`` and ``base_url`` can be obtained from the Wessex SDE
    team, and can be fed in here or saved with ``cynric.save_credentials()``.

    Args:
        dataset (Dataset | str | Path | dict[str, DataFrame]): Pre-prepared Valediction
            Dataset, a path to a CSV or folder of CSVs, or a dictionary of DataFrames.
        target_table_map (dict[str, str]): Mapping from dataset table names to Wessex
            SDE table names.
        chunk_size (int | None, optional): Maximum size of each data chunk
            in rows. This also makes use of Valediction's chunk importing,
            if data are not already imported. Defaults to ``10_000_000``.
        feedback (bool, optional): Whether to print and display progress
            information during the upload. Defaults to ``True``.
        import_data_first (bool, optional): If True, imports all data into
            the dataset from disk before uploading (if not yet imported).
            Defaults to ``False``, allowing ``chunk_size`` to propagate
            to Valediction.
        dictionary (Dictionary | str | Path | None): Pre-prepared Valediction Dictionary, or
            a filepath to a Valediction-compatible dictionary .xlsx file. Can be ignored
            if a Dataset is directly fed to ``data`` and has a dictionary already attached,
            otherwise must be provided.
        token (str, optional): Authentication token for the Wessex SDE API.
            If not provided, will be fetched from the OS credential storage
            if previously saved.
        base_url (str, optional): Base URL for the Wessex SDE API.
            If not provided, will be fetched from the OS credential storage
            if previously saved.

    Raises:
        DataIntegrityError: Raised from Valediction if there are data
            integrity issues.
        NoDictionaryError: Raised if no ``dictionary`` is provided and
            a Dataset complete with a dictionary is not provided to data
        Exception: Any error arising from chunk iteration, CSV conversion,
            or the underlying API calls will propagate.
        SecretNotSaved: If ``token`` or ``base_url`` are not provided and
            have not been saved to the OS credential storage.
    """
    # Instantiate Dataset (pre-prepared)
    if isinstance(dataset, Dataset):
        dataset = dataset
        if not dataset.dictionary:
            if dictionary is None:
                raise NoDictionaryError(
                    "A Dataset must already have a data dictionary attached, "
                    "or a `dictionary` argument must be provided to import one."
                )
            else:
                dataset.import_dictionary(dictionary)

    # Instantiate Dataset (fed as path or dictionary of DataFrames)
    if not isinstance(dataset, Dataset):
        if dictionary is None:
            raise NoDictionaryError(
                "When providing data as a path to data or dict of DataFrames, "
                "a `dictionary` argument must be provided to import a data dictionary."
            )
        else:
            dataset = vale.Dataset.create_from(dataset=dataset)
            dataset.import_dictionary(dictionary)

    uploader = Uploader(
        dataset=dataset,
        target_table_map=target_table_map,
        token=token,
        base_url=base_url,
    )
    if import_data_first:
        dataset.import_data()

    uploader.validate_and_upload(chunk_size=chunk_size, feedback=feedback)

    return dataset
