from cynric.uploading.uploading import Uploader
from cynric.uploading.convenience import validate_and_upload
from cynric.credentials.credentials import (
    save_credentials,
    delete_credentials,
    get_base_url,
    get_token,
)
from valediction.datasets.datasets import Dataset
from cynric.validation.validation import validate
from cynric import demo
from cynric.support.version_check import check_version
from cynric import instantiation as _instantiation
from cynric.dataset_manager.convenience import check_table_access

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
]
