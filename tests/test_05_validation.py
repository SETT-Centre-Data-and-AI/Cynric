import pytest  # noqa
import support as support  # noqa
from typing import Any  # noqa
from valediction.datasets.datasets import Dataset  # type: ignore
from valediction.exceptions import DataDictionaryError

from cynric.validation.validation import validate

# from cynric.val

# Helpers
# def helper_xxx() -> None:
#     pass


# # Fixtures
# @pytest.fixture(params=[None, "xxx"], ids=["test_none", "test_xxx"])
# def arg_name_xxx(request: pytest.FixtureRequest) -> Any:
#     return request.param


### ====================== ###
### ---------TESTS---------###
### ====================== ###


def test_validation_from_paths() -> None:
    validate(support.DEMO_DATA, support.DEMO_DICTIONARY)


def test_validation_passes() -> None:
    dataset = validate(support.DEMO_DATA, support.DEMO_DICTIONARY)
    dataset.check()


def test_validation_mixed() -> None:
    dataset = Dataset().create_from(support.DEMO_DATA)
    validate(dataset, dictionary=support.DEMO_DICTIONARY)


def test_validation_pre_prepared() -> None:
    dataset = Dataset().create_from(support.DEMO_DATA)
    dataset.import_dictionary(support.DEMO_DICTIONARY)
    validate(dataset)


def test_validation_pre_prepared_dictionary() -> None:
    dataset = Dataset().create_from(support.DEMO_DATA)
    dataset.import_dictionary(support.DEMO_DICTIONARY)
    validate(dataset, dataset.dictionary)


def test_validation_using_validiction() -> None:
    dataset = Dataset().create_from(support.DEMO_DATA)
    dataset.import_dictionary(support.DEMO_DICTIONARY)
    dataset.validate()  # no Cynric config override
    dataset.check()


def test_validation_path_no_dictionary_raises() -> None:
    with pytest.raises(DataDictionaryError):
        validate(support.DEMO_DATA)


def test_validation_dataset_no_dictionary_raises() -> None:
    dataset = Dataset().create_from(support.DEMO_DATA)
    with pytest.raises(DataDictionaryError):
        validate(dataset)


# Run
if __name__ == "__main__":
    pytest.main([__file__])
