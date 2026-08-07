from io import BytesIO
from types import SimpleNamespace

import pandas as pd
import pytest  # noqa
import support as support  # noqa
from support import (
    BAD_TOKEN,
    BAD_URL,
    DEMO_DATA,
    EXPIRED_TOKEN,
    GOOD_TOKEN,
    GOOD_URL,
    get_actual_table_map,
    get_dataset,
    get_incorrect_table_map,
    get_valid_table_map,
)
from valediction.datasets.datasets import Dataset  # type: ignore

from cynric.exceptions import (
    EmptyDatasetError,
    ExpiredTokenError,
    InvalidTokenError,
    InvalidUrlError,
    NoDictionaryError,
    UnvalidatedDatasetError,
)
from cynric.uploading.convenience import validate_and_upload  # noqa
from cynric.uploading.helpers import check_target_table_map
from cynric.uploading.uploading import Uploader  # noqa

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


def test_create_csv_in_memory_normalizes_headers_without_mutating_input() -> None:
    dataset = get_dataset()
    table_map = get_actual_table_map()
    uploader = Uploader(
        dataset=dataset, target_table_map=table_map, token=GOOD_TOKEN, base_url=GOOD_URL
    )
    source = pd.DataFrame([[1, 2]], columns=[" patient_id ", "mixed_Case"])

    csv_file = uploader._create_csv_in_memory(source)

    assert pd.read_csv(BytesIO(csv_file.getvalue())).columns.tolist() == [
        "PATIENT_ID",
        "MIXED_CASE",
    ]
    assert source.columns.tolist() == [" patient_id ", "mixed_Case"]


def test_upload_reports_transformed_headers_once_after_completion(capsys) -> None:
    class Item:
        name = "DEMOGRAPHICS"
        validated = True
        df = pd.DataFrame([[1], [2]], columns=[" patient_id "])

        def iterate_data_chunks(self, chunk_size):
            chunk = SimpleNamespace(
                df=pd.DataFrame([[1]], columns=[" patient_id "]),
                total_size=None,
                total_bytes_read=None,
                total_chunks_seen=None,
            )
            yield chunk
            yield chunk

    class Dataset:
        validated = True

        def __iter__(self):
            return iter([Item()])

        def __len__(self):
            return 1

    uploader = object.__new__(Uploader)
    uploader.dataset = Dataset()
    uploader.target_table_map = {"DEMOGRAPHICS": "target"}
    uploads = []
    uploader._upload_csv_chunk = lambda **kwargs: uploads.append(kwargs)

    uploader.upload(feedback=True)

    output = capsys.readouterr().out
    assert len(uploads) == 2
    assert (
        output.count("Note: some headers were transformed to uppercase (DEMOGRAPHICS).")
        == 1
    )


def test_upload_suppresses_transformation_note_when_feedback_disabled(capsys) -> None:
    class Item:
        name = "DEMOGRAPHICS"
        validated = True
        df = pd.DataFrame([[1]], columns=[" patient_id "])

        def iterate_data_chunks(self, chunk_size):
            yield SimpleNamespace(
                df=self.df,
                total_size=None,
                total_bytes_read=None,
                total_chunks_seen=None,
            )

    class Dataset:
        validated = True

        def __iter__(self):
            return iter([Item()])

        def __len__(self):
            return 1

    uploader = object.__new__(Uploader)
    uploader.dataset = Dataset()
    uploader.target_table_map = {"DEMOGRAPHICS": "target"}
    uploader._upload_csv_chunk = lambda **kwargs: None

    uploader.upload(feedback=False)

    assert "transformed to uppercase" not in capsys.readouterr().out


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
