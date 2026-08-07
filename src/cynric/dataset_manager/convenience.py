from pathlib import Path

from cynric.dataset_manager.navigator import Navigator


def check_table_access(
    search: str = "",
    token: str = "",
    base_url: str = "",
    include_datasets: bool = False,
    **kwargs,
) -> list[Path]:
    """Checks accessible Wessex SDE tables and folder structure, and the mapping of
    table name to 'ds000000' ID.

    Args:
        search (str, optional): Substring table name search filter.
            Defaults to "".
        token (str, optional): Token. Defaults to "" for retrieval from
            OS Credential Manager (if previously stored with `cynric.save_credentials`).
        base_url (str, optional): Base URL. Defaults to "" for retrieval from
            OS Credential Manager (if previously stored with `cynric.save_credentials`).
        include_datasets (bool, optional): Whether to include dataset folders in the search.
            Defaults to False.
        kwargs (dict, optional): Additional search arguments from
            `cynric.dataset_manager.navigator.search_dataset_folders()`, including
            `root_dir`, `include_datasets`, and `case_sensitive`. Defaults to None.
    """
    nav = Navigator(token=token, base_url=base_url)
    sorted_search = nav.search_dataset_folders(
        search=search, include_datasets=include_datasets, **kwargs
    )
    return sorted_search
