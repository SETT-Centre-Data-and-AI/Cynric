from pathlib import Path
import pytest

import valediction as vale
from valediction import demo
from cynric.forms import create_bc_forms, create_bc_dictionary

pd = pytest.importorskip("pandas")


def test_create_bc_dictionary_writes_forms_and_returns_ints(tmp_path: Path) -> None:

    path_to_dictionary = demo.DEMO_DICTIONARY
    dictionary = vale.import_dictionary(path_to_dictionary)

    out_dir = tmp_path / "forms"
    frames = create_bc_dictionary(dictionary, forms_output_dir=out_dir)

    assert (out_dir / "DEMOGRAPHICS.txt").is_file()
    assert (out_dir / "VITALS.txt").is_file()

    assert str(frames.columns["Key"].dtype) == "Int64"
    assert str(frames.columns["Length"].dtype) == "Int64"

    demographics_key = frames.columns.loc[
        (frames.columns["Table"] == "DEMOGRAPHICS")
        & (frames.columns["Column"] == "PATIENT_HASH"),
        "Key",
    ].iloc[0]
    assert demographics_key == 1


def test_create_bc_forms_normalizes_excel_int_columns(tmp_path: Path) -> None:
    pytest.importorskip("openpyxl")

    tables = pd.DataFrame(
        [
            ["DEMOGRAPHICS", "Demographic info"],
            ["VITALS", "Vitals"],
        ],
        columns=["Table", "Description"],
    )

    columns = pd.DataFrame(
        [
            ["PATIENT_HASH", "Text", 1, 12, None, "DEMOGRAPHICS", pd.NA, pd.NA],
            ["DATE_OF_BIRTH", "Date", pd.NA, pd.NA, None, "DEMOGRAPHICS", pd.NA, pd.NA],
            ["PATIENT_HASH", "Text", 1, 12, None, "VITALS", pd.NA, pd.NA],
            ["HEIGHT", "Float", pd.NA, pd.NA, None, "VITALS", pd.NA, pd.NA],
        ],
        columns=[
            "Column",
            "Data Type",
            "Key",
            "Length",
            "Column Description",
            "Table",
            "Choiceset",
            "Choiceset Index",
        ],
    )

    # Ensure it round-trips through Excel with float-like columns caused by NA.
    excel_path = tmp_path / "bc_dictionary.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        tables.to_excel(writer, sheet_name="Tables", index=False)
        columns.to_excel(writer, sheet_name="Columns", index=False)

    out_dir = tmp_path / "exported_forms"
    frames = create_bc_forms(excel_path, forms_output_dir=out_dir)

    assert str(frames.columns["Key"].dtype) == "Int64"
    assert str(frames.columns["Length"].dtype) == "Int64"

    assert (out_dir / "DEMOGRAPHICS.txt").is_file()
    assert (out_dir / "VITALS.txt").is_file()
