from collections.abc import Mapping

from valediction.datasets.datasets import Dataset  # type: ignore
from valediction.support import list_as_bullets  # type: ignore


def check_target_table_map(
    dataset: Dataset, target_table_map: Mapping[str, str]
) -> None:
    """Validates that target_table_map matches the tables in the dataset.

    This checks that:
    - `target_table_map` is a mapping of str to str.
    - All keys in `target_table_map` correspond to table names in `dataset`.
    - All table names in `dataset` are present as keys in `target_table_map`.

    Args:
        dataset (Dataset): Dataset containing data tables with a `.name` attribute.
        target_table_map (Mapping[str, str]): Mapping from dataset table names
            to target table names.

    Raises:
        TypeError: If `target_table_map` is not a mapping of `{str: str}`.
        ValueError: If the table names in `dataset` and `target_table_map`
            do not match exactly.
    """

    # Check type
    if not isinstance(target_table_map, Mapping):
        raise TypeError("target_table_map must be a mapping of {str: str}")

    # Check contents types
    for data_table_name, target_table in target_table_map.items():
        if not isinstance(data_table_name, str) or not isinstance(target_table, str):
            raise TypeError(
                "target_table_map must be a mapping of {str: str} "
                "as {data_table_name: target_sde_table}"
            )

    # Check integrity
    data_table_names = {item.name for item in dataset}
    target_table_map_names = set(target_table_map)

    missing_in_dataset = target_table_map_names - data_table_names
    missing_in_target_table_map = data_table_names - target_table_map_names

    # If missing
    if missing_in_dataset or missing_in_target_table_map:
        missing_in_dataset_str = list_as_bullets(sorted(missing_in_dataset))
        missing_in_target_table_map_str = list_as_bullets(
            sorted(missing_in_target_table_map)
        )

        missing_in_dataset_message = (
            f"Tables in target_table_map but missing from dataset:"
            f"{missing_in_dataset_str}\n"
            if missing_in_dataset
            else ""
        )
        missing_in_target_table_map_message = (
            f"Tables in dataset but missing from target_table_map:"
            f"{missing_in_target_table_map_str}"
            if missing_in_target_table_map
            else ""
        )

        raise ValueError(
            "Table names in the Dataset and target_table_map do not match.\n"
            f"{missing_in_dataset_message}"
            f"{missing_in_target_table_map_message}"
        )
