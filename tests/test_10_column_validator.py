import pandas as pd
import pytest

from cynric.utils import column_validator as cv


def test_validate_and_fix_column_name() -> None:
    col = "_bad col__"
    valid, reasons = cv.validate_column_name(col)

    assert valid is False
    assert {
        "Not uppercase",
        "Invalid characters",
        "Multiple underscores",
        "Edge underscores",
        "No leading letter",
    }.issubset(set(reasons))

    fixed = cv.fix_column_name_pipeline(col)
    assert fixed == "BAD_COL"


def test_fix_column_names_in_dataframe_preserves_original() -> None:
    df = pd.DataFrame([[1, 2]], columns=["col 1", "OK"])

    fixed = cv.fix_column_names_in_dataframe(df)

    assert list(fixed.columns) == ["COL_1", "OK"]
    assert list(df.columns) == ["col 1", "OK"]


# def test_check_true_duplicate_columns_and_fix() -> None:
#     df = pd.DataFrame(
#         [[1, 1, 2, 3], [1, 1, 4, 5]],
#         columns=["A", "A", "B", "B"],
#     )

#     groups = cv.check_true_duplicate_columns(df, fix=False)
#     assert groups == [["A", "A"]]

#     fixed = cv.check_true_duplicate_columns(df, fix=True)
#     assert list(fixed.columns) == ["A", "B", "B"]
#     assert fixed.shape[1] == 3


def test_validate_table_autofix() -> None:
    df = pd.DataFrame([[1, 2]], columns=["bad col", "OK"])

    out_df, valid, modified = cv.validate_table(df, autofix_columns=False)

    assert out_df is df
    assert valid is False
    assert modified is False

    fixed_df, valid, modified = cv.validate_table(df, autofix_columns=True)

    assert list(fixed_df.columns) == ["BAD_COL", "OK"]
    assert valid is True
    assert modified is True


def test_validate_tables_with_reporter_details_and_results() -> None:
    df1 = pd.DataFrame([[1, 2]], columns=["A", "B"])
    df2 = pd.DataFrame([[3]], columns=["bad col"])
    df1.attrs["name"] = "T1"
    df2.attrs["name"] = "T2"
    reporter = cv.Reporter(cv.Verbosity.none)

    results, mappings = cv.validate_tables_with_reporter(
        [df1, df2],
        reporter=reporter,
        autofix_columns=True,
    )

    assert len(results) == 2
    assert len(reporter.entries) == 2
    assert reporter.entries[0].filename == "T1"
    assert reporter.entries[1].filename == "T2"
    assert len(reporter.entries[0].column_details) == 2
    assert len(reporter.entries[1].column_details) == 1
    assert list(results[1][0].columns) == ["BAD_COL"]
    assert mappings["T1"] == {"A": "A", "B": "B"}
    assert mappings["T2"] == {"bad col": "BAD_COL"}


if __name__ == "__main__":
    pytest.main([__file__])
