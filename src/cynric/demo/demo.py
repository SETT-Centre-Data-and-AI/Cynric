from valediction import demo as vale_demo  # type: ignore
from valediction.datasets.datasets import Dataset  # type: ignore

from cynric.uploading.convenience import validate_and_upload

DEMO_DATA = vale_demo.DEMO_DATA
DEMO_DICTIONARY = vale_demo.DEMO_DICTIONARY


def push_demo_data(
    target_table_map: dict[str, str],
    token: str = "",
    base_url: str = "",
    chunk_size: int = 10_000_000,
) -> Dataset:
    """Demo/test function to push the Cynric demo dataset to the Wessex SDE.

    Requires a Wessex SDE ``token`` and ``base_url`` to be provided or previously
    saved via ``cynric.save_credentials()``. Also requires a ``target_table_map``
    dictionary that maps demo dataset tables to established Wessex SDE Demo tables.

    The Wessex SDE will first need to establish and grant access to these demo tables
    before the dataset can be uploaded.

    Args:
        target_table_map (dict[str, str]): Mapping from dataset table names
            to Wessex SDE table names.
        token (str, optional): Authentication token for the Wessex SDE API.
            If not provided, will be fetched from the OS credential storage
            if previously saved.
        base_url (str, optional): Base URL for the Wessex SDE API.
            If not provided, will be fetched from the OS credential storage
            if previously saved.
        chunk_size (int | None, optional): Maximum size of each data chunk
            in rows. This also makes use of Valediction's chunk importing,
            if data are not already imported. Defaults to ``10_000_000``.

    Returns:
        Dataset: Demo dataset returned after upload
    """
    dataset = import_demo_data()
    dataset = validate_and_upload(
        dataset,
        target_table_map,
        token=token,
        base_url=base_url,
        chunk_size=chunk_size,
    )
    return dataset


def import_demo_data() -> Dataset:
    """Demo/test function to import the Valediction demo dataset.

    Returns:
        Dataset: Demo dataset
    """
    dataset = Dataset().create_from(DEMO_DATA)
    dataset.import_dictionary(DEMO_DICTIONARY)
    dataset.import_data()
    return dataset
