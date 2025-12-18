import pytest  # noqa
import support as support  # noqa
from cynric.uploading.helpers import check_target_table_map
from cynric.uploading.uploading import Uploader  # noqa
from cynric.uploading.convenience import validate_and_upload  # noqa
from valediction.datasets.datasets import Dataset  # type: ignore
from cynric.exceptions import (
    InvalidTokenError,
    UnvalidatedDatasetError,
    EmptyDatasetError,
    NoDictionaryError,
    InvalidUrlError,
    ExpiredTokenError,
)

from support import (
    GOOD_URL,
    GOOD_TOKEN,
    BAD_URL,
    BAD_TOKEN,
    EXPIRED_TOKEN,
    DEMO_DATA,
    get_dataset,
    get_valid_table_map,
    get_actual_table_map,
    get_incorrect_table_map,
)

### ====================== ###
### ---------TESTS---------###
### ====================== ###


# Basic tests
def test_dataset() -> None:
    get_dataset()


def test_correct_table_map() -> None:
    table_map = get_valid_table_map()
    check_target_table_map(get_dataset(), table_map)


def test_incorrect_table_map_raises() -> None:
    table_map = get_incorrect_table_map()
    with pytest.raises(ValueError):
        check_target_table_map(get_dataset(), table_map)


# Test Uploader instantiation
def test_uploader_instantiation() -> None:
    dataset = get_dataset()
    table_map = get_valid_table_map()
    _ = Uploader(
        dataset=dataset, target_table_map=table_map, token=GOOD_TOKEN, base_url=GOOD_URL
    )


def test_uploader_instantiation_with_bad_url() -> None:
    dataset = get_dataset()
    table_map = get_valid_table_map()
    with pytest.raises(InvalidUrlError):
        _ = Uploader(
            dataset=dataset,
            target_table_map=table_map,
            token=GOOD_TOKEN,
            base_url=BAD_URL,
        )


def test_uploader_instantiation_with_bad_token() -> None:
    dataset = get_dataset()
    table_map = get_valid_table_map()
    with pytest.raises(InvalidTokenError):
        _ = Uploader(
            dataset=dataset,
            target_table_map=table_map,
            token=BAD_TOKEN,
            base_url=GOOD_URL,
        )


def test_uploader_instantiation_with_expired_token() -> None:
    dataset = get_dataset()
    table_map = get_valid_table_map()
    with pytest.raises(ExpiredTokenError):
        _ = Uploader(
            dataset=dataset,
            target_table_map=table_map,
            token=EXPIRED_TOKEN,
            base_url=GOOD_URL,
        )


def test_uploader_instantiation_with_bad_map() -> None:
    dataset = get_dataset()
    table_map = get_incorrect_table_map()
    with pytest.raises(ValueError):
        _ = Uploader(dataset=dataset, target_table_map=table_map)


def test_uploader_instantiation_with_bad_dataset() -> None:
    dataset = Dataset()
    table_map = get_valid_table_map()
    with pytest.raises(EmptyDatasetError):
        _ = Uploader(dataset=dataset, target_table_map=table_map)


# Test Uploading
def test_uploading_unvalidated_dataset() -> None:
    dataset = get_dataset()
    table_map = get_actual_table_map()
    uploader = Uploader(
        dataset=dataset, target_table_map=table_map, token=GOOD_TOKEN, base_url=GOOD_URL
    )
    with pytest.raises(UnvalidatedDatasetError):
        uploader.upload(feedback=False)


def test_validate_and_upload_no_dictionary() -> None:
    dataset = DEMO_DATA
    with pytest.raises(NoDictionaryError):
        validate_and_upload(
            dataset=dataset, target_table_map=get_actual_table_map(), feedback=False
        )


def test_validate_and_upload_no_dictionary_direct() -> None:
    dataset = Dataset().create_from(DEMO_DATA)
    with pytest.raises(NoDictionaryError):
        validate_and_upload(
            dataset=dataset, target_table_map=get_actual_table_map(), feedback=False
        )


# Run
if __name__ == "__main__":
    pytest.main([__file__])
