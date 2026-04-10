from valediction.convenience import create_dataset
from valediction.datasets.datasets import Dataset

from cynric import demo
from cynric import instantiation as _instantiation
from cynric.credentials.credentials import (
    delete_credentials,
    get_base_url,
    get_token,
    save_credentials,
)
from cynric.dataset_manager.convenience import check_table_access
from cynric.support.version_check import check_version
from cynric.uploading.convenience import validate_and_upload
from cynric.uploading.uploading import Uploader
from cynric.validation.validation import validate

_instantiation.inject_cynric_variables()
check_version()


__all__ = [
    "Uploader",
    "validate_and_upload",
    "save_credentials",
    "delete_credentials",
    "get_base_url",
    "get_token",
    "Dataset",
    "validate",
    "demo",
    "check_table_access",
    "create_dataset",
]
