import pytest  # noqa
import support as support  # noqa
from typing import Any  # noqa
import numpy as np
import importlib

from valediction.datasets.datasets import Dataset
from valediction.data_types.data_types import DataType
from valediction.demo import DEMO_DATA, DEMO_DICTIONARY
from valediction.validation.issues import IssueType, Range
from valediction.exceptions import DataIntegrityError


# Helpers
def create_dataset() -> Dataset:
    dataset = Dataset.create_from(DEMO_DATA)
    dataset.import_dictionary(DEMO_DICTIONARY)
    return dataset


def create_dataset_imported() -> Dataset:
    dataset = create_dataset()
    dataset.import_data()
    return dataset


def _expand_ranges(ranges: list[Range]) -> set[int]:
    rows: set[int] = set()
    for r in ranges:
        rows.update(range(r.start, r.end + 1))
    return rows


# Fixtures
@pytest.fixture(autouse=True)
def _isolate_injection():  # noqa
    """Clean Valediction's global config + injected variables between tests."""
    from valediction.integrity import inject_config_variables, reset_default_config

    inject_config_variables({})
    reset_default_config()
    yield
    inject_config_variables({})
    reset_default_config()


@pytest.fixture()
def _restore_cynric_variables():  # noqa
    """Prevent CYNRIC_VARIABLES mutations leaking across tests."""
    from cynric.instantiation import CYNRIC_VARIABLES

    snapshot = dict(CYNRIC_VARIABLES)
    yield
    CYNRIC_VARIABLES.clear()
    CYNRIC_VARIABLES.update(snapshot)


### ====================== ###
### ---------TESTS---------###
### ====================== ###


def test_raises_integer_out_of_range_no_overlap():
    dataset = create_dataset_imported()

    import cynric

    importlib.reload(cynric)  # reload import to ensure allow_bigint default override

    from valediction import get_config

    assert get_config().allow_bigint is False

    # Pick a stable demo column and force it to INTEGER in the dictionary
    TABLE = "VITALS"
    COLUMN = "RESULT"

    item = dataset[TABLE]
    table_dictionary = item.table_dictionary
    col = table_dictionary.get_column(COLUMN)
    col.data_type = DataType.INTEGER
    col.length = None

    df = item.data
    n = len(df)
    df[COLUMN] = np.arange(n, dtype="int64").astype("object")

    # Inject known offenders (and one known good boundary)
    df.loc[0, COLUMN] = "2147483648"  # out of range (too big)
    df.loc[1, COLUMN] = "not_an_int"  # type mismatch
    df.loc[2, COLUMN] = "2147483647"  # ok (max int4)
    df.loc[3, COLUMN] = "-2147483649"  # out of range (too small)
    df.loc[4, COLUMN] = "3.14"  # type mismatch

    with pytest.raises(DataIntegrityError):
        dataset.validate()
        dataset.check()

    # Pull issues for this specific table/column
    type_mismatch_issues = [
        issue
        for issue in item.validator.issues
        if issue.type == IssueType.TYPE_MISMATCH
        and issue.table == TABLE
        and issue.column == COLUMN
    ]
    out_of_range_issues = [
        issue
        for issue in item.validator.issues
        if issue.type == IssueType.INTEGER_OUT_OF_RANGE
        and issue.table == TABLE
        and issue.column == COLUMN
    ]

    assert type_mismatch_issues, "Expected TYPE_MISMATCH issue for integer column"
    assert out_of_range_issues, "Expected INTEGER_OUT_OF_RANGE issue for integer column"

    # Exact ranges we injected (ensure stability + no accidental spread)
    assert type_mismatch_issues[0].ranges == [Range(1, 1), Range(4, 4)]
    assert out_of_range_issues[0].ranges == [Range(0, 0), Range(3, 3)]

    # Ensure they don't overlap at the row level
    tm_rows = _expand_ranges(type_mismatch_issues[0].ranges)
    oor_rows = _expand_ranges(out_of_range_issues[0].ranges)
    assert tm_rows.isdisjoint(oor_rows)


# Run
if __name__ == "__main__":
    pytest.main([__file__])
