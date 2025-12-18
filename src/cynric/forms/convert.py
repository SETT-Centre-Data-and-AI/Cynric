from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from valediction.data_types.data_types import DataType
from valediction.dictionary.importing import import_dictionary
from valediction.dictionary.model import Dictionary

try:
    import pandas as pd
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "cynric.forms requires `pandas` (and typically `openpyxl` for exports). "
        "Install with `pip install pandas openpyxl`."
    ) from exc

from .create import create_form

TypeConverter = Callable[[Any], str]


def _as_int_flag(value: Any) -> int | None:
    if value is None:
        return None
    return int(bool(value))


def _as_optional_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@dataclass(frozen=True, slots=True)
class BCDictionaryFrames:
    tables: pd.DataFrame
    columns: pd.DataFrame


_BC_TYPE_MAPPING: dict[DataType, str] = {
    DataType.TEXT: "Text",
    DataType.INTEGER: "Integer",
    DataType.FLOAT: "Float",
    DataType.DATE: "Date",
    DataType.DATETIME: "Timestamp",
}


def _convert_to_bc_type(data_type: DataType) -> str:
    return _BC_TYPE_MAPPING[data_type]


def _build_bc_dictionary_frames(
    dictionary: Dictionary,
    *,
    type_converter: TypeConverter = _convert_to_bc_type,
) -> BCDictionaryFrames:
    """Build BC dictionary tables for all tables/columns in `dictionary`.

    Returns dataframes compatible with `cynric.forms.creator.create_form()`:
      - tables: ['Table', 'Description']
      - columns: ['Column', 'Data Type', 'Key', 'Length', 'Column Description',
                 'Table', 'Choiceset', 'Choiceset Index']
    """

    table_rows: list[list[Any]] = []
    column_rows: list[list[Any]] = []

    for table_name in dictionary.get_table_names():
        table = dictionary.get_table(table_name)
        table_rows.append([table.name, getattr(table, "description", None)])

        for column in table:
            key_value = _as_int_flag(getattr(column, "primary_key", None))
            length_value = _as_optional_int(getattr(column, "length", None))

            column_rows.append(
                [
                    column.name,
                    type_converter(getattr(column, "data_type", None)),
                    key_value,
                    length_value,
                    getattr(column, "description", None),
                    table.name,
                    pd.NA,  # Choiceset
                    pd.NA,  # Choiceset Index
                ]
            )

    tables = pd.DataFrame(table_rows, columns=["Table", "Description"])

    columns = pd.DataFrame(
        column_rows,
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

    for int_col in ("Key", "Length", "Choiceset Index"):
        if int_col in columns.columns:
            columns[int_col] = columns[int_col].astype("Int64")

    return BCDictionaryFrames(tables=tables, columns=columns)


def _load_bc_dictionary_excel(
    excel_path: str | Path,
    *,
    tables_sheet: str = "Tables",
    columns_sheet: str = "Columns",
) -> BCDictionaryFrames:
    """Load a BC dictionary export (XLSX) into tables/columns dataframes.

    Expected sheet names default to 'Tables' and 'Columns' (matching
    `export_bc_dictionary()` usage in this package).
    """

    exported = pd.read_excel(excel_path, sheet_name=[tables_sheet, columns_sheet])

    try:
        tables = exported[tables_sheet]
    except KeyError as exc:
        raise KeyError(
            f"Missing sheet {tables_sheet!r} in {str(excel_path)!r}; found {list(exported)}"
        ) from exc

    try:
        columns = exported[columns_sheet]
    except KeyError as exc:
        raise KeyError(
            f"Missing sheet {columns_sheet!r} in {str(excel_path)!r}; found {list(exported)}"
        ) from exc

    columns = _normalize_bc_dictionary_column_dtypes(columns)

    return BCDictionaryFrames(tables=tables, columns=columns)


def _normalize_bc_dictionary_column_dtypes(columns: pd.DataFrame) -> pd.DataFrame:
    normalized = columns.copy()

    for int_col in ("Key", "Length", "Choiceset Index"):
        if int_col not in normalized.columns:
            continue
        normalized[int_col] = pd.to_numeric(
            normalized[int_col], errors="coerce"
        ).astype("Int64")

    return normalized


def _export_bc_dictionary(
    output_dir: str | Path,
    sheets: dict[str, pd.DataFrame],
    *,
    index: bool = False,
) -> Path:
    output_dir = Path(output_dir)

    with pd.ExcelWriter(output_dir, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=index)

    return output_dir


def create_bc_forms(
    excel_path: str | Path,
    *,
    forms_output_dir: str | Path | None,
    tables_sheet: str = "Tables",
    columns_sheet: str = "Columns",
) -> BCDictionaryFrames:
    """Create BC form files from an exported dictionary XLSX.

    This is the inverse of `create_forms_from_dictionary(..., export_excel_path=...)`:
    it reads the XLSX and re-generates per-table form `.txt` files.
    """

    frames = _load_bc_dictionary_excel(
        excel_path, tables_sheet=tables_sheet, columns_sheet=columns_sheet
    )

    for table_name, table_column_details in frames.columns.groupby("Table"):
        create_form(
            form_name=str(table_name),
            table_details=frames.tables,
            column_details=table_column_details.reset_index(drop=True),
            table_name=str(table_name),
            output_dir=forms_output_dir,
        )

    return frames


def create_bc_dictionary(
    dictionary: Dictionary | Path | str,
    *,
    forms_output_dir: str | Path | None,
    type_converter: TypeConverter = _convert_to_bc_type,
    export_excel_path: str | Path | None = None,
) -> BCDictionaryFrames:
    """Create BC form files for every table in `dictionary`.

    If `export_excel_path` is provided, also writes a 2-sheet XLSX with 'Tables'
    and 'Columns' dataframes.
    """
    if isinstance(dictionary, (str, Path)):
        dictionary = import_dictionary(dictionary)

    frames = _build_bc_dictionary_frames(dictionary, type_converter=type_converter)

    for table_name in dictionary.get_table_names():
        table = dictionary.get_table(table_name)
        table_column_details = frames.columns[frames.columns["Table"] == table.name]
        table_column_details = table_column_details.reset_index(drop=True)

        create_form(
            form_name=table.name,
            table_details=frames.tables,
            column_details=table_column_details,
            table_name=table.name,
            output_dir=forms_output_dir,
        )

    if export_excel_path is not None:
        _export_bc_dictionary(
            export_excel_path,
            sheets={"Tables": frames.tables, "Columns": frames.columns},
        )

    return frames
