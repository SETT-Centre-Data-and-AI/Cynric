import pytest
import support as support
from pandas import DataFrame
from valediction.convenience import create_dataset, validate
from valediction.datasets.datasets import Dataset
from valediction.dictionary.model import Dictionary


# Helpers
def get_demo_dataframes() -> tuple[dict[str, DataFrame], Dictionary]:
    dataset = create_dataset(support.DEMO_DATA, support.DEMO_DICTIONARY)
    dataset.import_data()
    dataframes = {item.name: item.data.copy() for item in dataset}
    return dataframes, dataset.dictionary


# Fixtures
@pytest.fixture()
def demo_dataframes() -> tuple[dict[str, DataFrame], Dictionary]:
    return get_demo_dataframes()


### ====================== ###
### ---------TESTS---------###
### ====================== ###


@pytest.mark.parametrize(
    ("data", "dictionary"),
    [
        (str(support.DEMO_DATA), support.DEMO_DICTIONARY),
        (support.DEMO_DATA, str(support.DEMO_DICTIONARY)),
    ],
)
def test_create_dataset_from_path_types(data, dictionary) -> None:
    dataset = create_dataset(data, dictionary)

    assert isinstance(dataset, Dataset)
    assert len(dataset) == 4
    assert dataset.dictionary is not None


def test_create_dataset_from_dataframe_mapping(
    demo_dataframes: tuple[dict[str, DataFrame], Dictionary],
) -> None:
    dataframes, dictionary = demo_dataframes

    dataset = create_dataset(dataframes, dictionary)

    assert isinstance(dataset, Dataset)
    assert set(item.name for item in dataset) == set(dataframes)
    assert dataset.dictionary is not None


def test_create_dataset_without_dictionary() -> None:
    dataset = create_dataset(support.DEMO_DATA)

    assert isinstance(dataset, Dataset)
    assert len(dataset) == 4
    assert dataset.dictionary is None


@pytest.mark.parametrize(
    ("data", "dictionary"),
    [
        (str(support.DEMO_DATA), support.DEMO_DICTIONARY),
        (support.DEMO_DATA, str(support.DEMO_DICTIONARY)),
    ],
)
def test_validate_from_path_types(data, dictionary) -> None:
    dataset = validate(data, dictionary, feedback=False)

    assert isinstance(dataset, Dataset)
    dataset.check()


def test_validate_dataframe_mapping_with_dictionary_object(
    demo_dataframes: tuple[dict[str, DataFrame], Dictionary],
) -> None:
    dataframes, dictionary = demo_dataframes

    dataset = validate(dataframes, dictionary, feedback=False)

    assert isinstance(dataset, Dataset)
    dataset.check()


def test_validate_prepared_dataset_without_dictionary_argument() -> None:
    dataset = create_dataset(support.DEMO_DATA, support.DEMO_DICTIONARY)

    validated_dataset = validate(dataset, feedback=False)

    assert validated_dataset is dataset
    validated_dataset.check()


# Run
if __name__ == "__main__":
    pytest.main([__file__])
