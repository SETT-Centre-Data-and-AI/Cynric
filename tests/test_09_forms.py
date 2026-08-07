from pathlib import Path

import pytest
import valediction as vale
from valediction import demo
from valediction.datasets.datasets import Dataset  # type: ignore

from cynric.forms import create_bc_files
from cynric.forms.convert import create_forms_from_bc_dictionary
from cynric.forms.create import create_form

pd = pytest.importorskip("pandas")


def _get_test_artifacts_dir() -> Path:
    artifacts_dir = Path(__file__).resolve().parent / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return artifacts_dir


def test_create_bc_dictionary_writes_forms_and_returns_ints() -> None:

    path_to_dictionary = demo.DEMO_DICTIONARY
    dictionary = vale.import_dictionary(path_to_dictionary)

    out_dir = _get_test_artifacts_dir() / "bc_dictionary_forms"
    frames = create_bc_files(dictionary, forms_output_dir=out_dir)

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


def test_create_bc_forms_normalizes_excel_int_columns() -> None:
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
            ["VISIT_ID", "Integer", 1, 8, None, "DEMOGRAPHICS", pd.NA, pd.NA],
            ["DATE_OF_BIRTH", "Date", pd.NA, pd.NA, None, "DEMOGRAPHICS", pd.NA, pd.NA],
            ["SEX", "Text", pd.NA, 1, None, "DEMOGRAPHICS", pd.NA, pd.NA],
            ["ZIP_CODE", "Text", pd.NA, 5, None, "DEMOGRAPHICS", pd.NA, pd.NA],
            ["PATIENT_HASH", "Text", 1, 12, None, "VITALS", pd.NA, pd.NA],
            ["VISIT_ID", "Integer", 1, 8, None, "VITALS", pd.NA, pd.NA],
            ["MEASURED_AT", "Timestamp", pd.NA, pd.NA, None, "VITALS", pd.NA, pd.NA],
            ["HEIGHT", "Float", pd.NA, pd.NA, None, "VITALS", pd.NA, pd.NA],
            ["WEIGHT", "Float", pd.NA, pd.NA, None, "VITALS", pd.NA, pd.NA],
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
    excel_path = _get_test_artifacts_dir() / "bc_dictionary.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        tables.to_excel(writer, sheet_name="Tables", index=False)
        columns.to_excel(writer, sheet_name="Columns", index=False)

    out_dir = _get_test_artifacts_dir() / "bc_dictionary_exported_forms"
    frames = create_forms_from_bc_dictionary(excel_path, forms_output_dir=out_dir)

    assert str(frames.columns["Key"].dtype) == "Int64"
    assert str(frames.columns["Length"].dtype) == "Int64"

    demographics_keys = frames.columns.loc[
        frames.columns["Table"] == "DEMOGRAPHICS", "Key"
    ]
    vitals_keys = frames.columns.loc[frames.columns["Table"] == "VITALS", "Key"]
    assert demographics_keys.notna().sum() == 2
    assert vitals_keys.notna().sum() == 2

    assert (out_dir / "DEMOGRAPHICS.txt").is_file()
    assert (out_dir / "VITALS.txt").is_file()


def test_create_bc_forms_sanitizes_and_truncates_descriptions() -> None:
    pytest.importorskip("openpyxl")

    long_table_description = ("A" * 248) + "\nXYZ"
    long_column_description = ("B" * 248) + "\nZZZ"

    tables = pd.DataFrame(
        [["DEMOGRAPHICS", long_table_description]],
        columns=["Table", "Description"],
    )

    columns = pd.DataFrame(
        [
            [
                "PATIENT_HASH",
                "Text",
                1,
                12,
                long_column_description,
                "DEMOGRAPHICS",
                pd.NA,
                pd.NA,
            ]
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

    excel_path = _get_test_artifacts_dir() / "bc_dictionary_long_descriptions.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        tables.to_excel(writer, sheet_name="Tables", index=False)
        columns.to_excel(writer, sheet_name="Columns", index=False)

    out_dir = _get_test_artifacts_dir() / "bc_dictionary_long_description_forms"
    frames = create_forms_from_bc_dictionary(excel_path, forms_output_dir=out_dir)

    table_description = frames.tables.loc[0, "Description"]
    column_description = frames.columns.loc[0, "Column Description"]

    assert len(table_description) == 250
    assert len(column_description) == 250
    assert table_description.endswith("...")
    assert column_description.endswith("...")
    assert "\n" not in table_description
    assert "\n" not in column_description

    generated_form = (out_dir / "DEMOGRAPHICS.txt").read_text()
    assert table_description in generated_form
    assert column_description in generated_form
    assert long_table_description not in generated_form
    assert long_column_description not in generated_form


def test_create_form_normalizes_emitted_names_without_mutating_inputs(tmp_path) -> None:
    tables = pd.DataFrame(
        [["  demo table  ", "Description"]], columns=["Table", "Description"]
    )
    columns = pd.DataFrame(
        [
            [
                "  patient id ",
                "Text",
                1,
                12,
                "Identifier",
                "  demo table  ",
                pd.NA,
                pd.NA,
            ]
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

    create_form(
        form_name="  demo table  ",
        table_details=tables,
        column_details=columns,
        table_name="  demo table  ",
        output_dir=tmp_path,
    )

    generated_form = (tmp_path / "DEMO TABLE.txt").read_text()
    assert "name=DEMO TABLE" in generated_form
    assert "PATIENT ID\tIdentifier" in generated_form
    assert list(tables["Table"]) == ["  demo table  "]
    assert list(columns["Column"]) == ["  patient id "]


def test_create_bc_files_reports_transformed_headers(capsys, monkeypatch) -> None:
    tables = pd.DataFrame(
        [[" demographics ", "Description"], ["vitals", "Vitals"]],
        columns=["Table", "Description"],
    )
    columns = pd.DataFrame(
        [
            [
                " patient_id ",
                "Text",
                1,
                12,
                "Identifier",
                " demographics ",
                pd.NA,
                pd.NA,
            ],
            ["weight", "Float", pd.NA, pd.NA, "Weight", "vitals", pd.NA, pd.NA],
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

    class Table:
        def __init__(self, name):
            self.name = name

        def __iter__(self):
            return iter([])

    class Dictionary:
        def get_table_names(self):
            return [" demographics ", "vitals"]

        def get_table(self, name):
            return Table(name)

    from cynric.forms import convert

    frames = type("Frames", (), {"tables": tables, "columns": columns})()
    monkeypatch.setattr(
        convert,
        "_build_bc_dictionary_frames",
        lambda dictionary, type_converter: frames,
    )

    create_bc_files(Dictionary(), forms_output_dir=None)

    assert (
        "Note: some headers were transformed to uppercase (DEMOGRAPHICS, VITALS)."
        in capsys.readouterr().out
    )


def test_create_bc_files_does_not_report_standardized_headers(
    capsys, monkeypatch
) -> None:
    tables = pd.DataFrame(
        [["DEMOGRAPHICS", "Description"]], columns=["Table", "Description"]
    )
    columns = pd.DataFrame(
        [["PATIENT_ID", "Text", 1, 12, "Identifier", "DEMOGRAPHICS", pd.NA, pd.NA]],
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

    class Table:
        name = "DEMOGRAPHICS"

        def __iter__(self):
            return iter([])

    class Dictionary:
        def get_table_names(self):
            return ["DEMOGRAPHICS"]

        def get_table(self, name):
            return Table()

    from cynric.forms import convert

    frames = type("Frames", (), {"tables": tables, "columns": columns})()
    monkeypatch.setattr(
        convert,
        "_build_bc_dictionary_frames",
        lambda dictionary, type_converter: frames,
    )
    create_bc_files(Dictionary(), forms_output_dir=None)

    assert "transformed to uppercase" not in capsys.readouterr().out


def test_create_bc_files_from_dummy_dictionary_exports_excel() -> None:
    pytest.importorskip("openpyxl")

    demographics = pd.DataFrame(
        [
            ["PAT-0001", "PRAC-01", "1985-04-12", "F", "BS1 4AB"],
            ["PAT-0002", "PRAC-01", "1973-11-03", "M", "BS1 4AB"],
            ["PAT-0003", "PRAC-02", "1990-07-29", "F", "BS2 7CD"],
        ],
        columns=[
            "PATIENT_ID",
            "PRACTICE_ID",
            "DATE_OF_BIRTH",
            "SEX",
            "POSTCODE",
        ],
    )

    visits = pd.DataFrame(
        [
            ["PAT-0001", "V-1001", "2024-01-15", 172.4, 71.2],
            ["PAT-0001", "V-1002", "2024-06-18", 172.4, 70.1],
            ["PAT-0002", "V-2001", "2024-03-03", 180.2, 84.0],
            ["PAT-0003", "V-3001", "2024-05-22", 165.0, 62.5],
        ],
        columns=["PATIENT_ID", "VISIT_ID", "VISIT_DATE", "HEIGHT_CM", "WEIGHT_KG"],
    )

    dataset = Dataset.create_from({"DEMOGRAPHICS": demographics, "VISITS": visits})

    primary_keys = {
        "DEMOGRAPHICS": ["PATIENT_ID", "PRACTICE_ID"],
        "VISITS": ["PATIENT_ID", "VISIT_ID"],
    }
    dictionary = dataset.generate_dictionary(primary_keys=primary_keys)
    dataset.import_dictionary(dictionary)

    artifacts_dir = _get_test_artifacts_dir()
    forms_dir = artifacts_dir / "dummy_bc_forms"
    excel_path = artifacts_dir / "dummy_bc_dictionary.xlsx"

    frames = create_bc_files(
        dictionary, forms_output_dir=forms_dir, export_excel_path=excel_path
    )

    assert (forms_dir / "DEMOGRAPHICS.txt").is_file()
    assert (forms_dir / "VISITS.txt").is_file()
    assert excel_path.is_file()

    assert str(frames.columns["Key"].dtype) == "Int64"
    assert str(frames.columns["Length"].dtype) == "Int64"

    demographics_keys = frames.columns.loc[
        frames.columns["Table"] == "DEMOGRAPHICS", ["Column", "Key"]
    ].set_index("Column")["Key"]
    visits_keys = frames.columns.loc[
        frames.columns["Table"] == "VISITS", ["Column", "Key"]
    ].set_index("Column")["Key"]

    assert demographics_keys["PATIENT_ID"] == 1
    assert demographics_keys["PRACTICE_ID"] == 2
    assert visits_keys["PATIENT_ID"] == 1
    assert visits_keys["VISIT_ID"] == 2
