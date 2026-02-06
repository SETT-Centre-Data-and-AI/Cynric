import json
import re
from collections import defaultdict
from enum import IntEnum

# from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple, Iterable
import pandas as pd
from tabulate import tabulate

# from bc_platforms.forms.utils import load_df_by_filetype

# Maximum allowed length for a column name.
MAX_COLUMN_NAME_LENGTH = 30


class Verbosity(IntEnum):
    none = 0
    default = 1
    verbose = 2


class ColumnNameValidator:
    """
    Encapsulates validation and fixing logic for column names.

    Attributes:
      - config: which steps to apply.
    """

    def __init__(self, config: Optional[Dict[str, bool]] = None):
        default = {
            "uppercase": True,
            "fix_invalid": True,
            "collapse_underscores": True,
            "strip_edges": True,
            "ensure_letter": True,
            "trim_length": True,
        }
        self.config = default if config is None else {**default, **config}

    # --- Transformation helpers ---
    def _to_upper(self, col: str) -> str:
        return col.upper()

    def _fix_invalid_chars(self, col: str) -> str:
        return re.sub(r"[^A-Z0-9_]", "_", col)

    def _collapse_underscores(self, col: str) -> str:
        return re.sub(r"_+", "_", col)

    def _strip_edge_underscores(self, col: str) -> str:
        return col.strip("_")

    def _ensure_leading_letter(self, col: str) -> str:
        if not col or not col[0].isalpha():
            col = "COL_" + col
        return col

    def _trim_to_length(self, col: str) -> str:
        return col[:MAX_COLUMN_NAME_LENGTH]

    # --- Public API ---
    def validate(self, col: str) -> Tuple[bool, List[str]]:
        """
        Returns (is_valid, reasons) for a column name.
        """
        reasons: List[str] = []
        if self.config.get("uppercase", True) and col != col.upper():
            reasons.append("Not uppercase")
        if self.config.get("fix_invalid", True) and re.search(r"[^A-Z0-9_]", col):
            reasons.append("Invalid characters")
        if self.config.get("collapse_underscores", True) and "__" in col:
            reasons.append("Multiple underscores")
        if self.config.get("strip_edges", True) and (
            col.startswith("_") or col.endswith("_")
        ):
            reasons.append("Edge underscores")
        if self.config.get("ensure_letter", True) and (not col or not col[0].isalpha()):
            reasons.append("No leading letter")
        if self.config.get("trim_length", True) and len(col) > MAX_COLUMN_NAME_LENGTH:
            reasons.append("Too long")
        return not reasons, reasons

    def fix(self, col: str) -> str:
        """
        Applies configured transformations to fix a column name.
        """
        col = str(col)
        steps = [
            ("uppercase", self._to_upper),
            ("fix_invalid", self._fix_invalid_chars),
            ("collapse_underscores", self._collapse_underscores),
            ("strip_edges", self._strip_edge_underscores),
            ("ensure_letter", self._ensure_leading_letter),
            ("trim_length", self._trim_to_length),
        ]
        for key, fn in steps:
            if self.config.get(key, True):
                col = fn(col)
        return col


class ReportEntry:
    """
    Captures validation/fix per file.
    """

    def __init__(self, filename: str, column_details: List[Dict[str, Any]]):
        self.filename = filename
        self.column_details = column_details

    @property
    def total_cols(self) -> int:
        return len(self.column_details)

    @property
    def fixed_cols(self) -> int:
        return sum(1 for c in self.column_details if c["original"] != c["fixed"])

    @property
    def reasons_summary(self) -> List[str]:
        return sorted({r for c in self.column_details for r in c["reasons"]})


class Reporter:
    """
    Builds and prints:
      1) Summary report
      2) Table breakdown
      3) Column breakdown (verbose)
    """

    def __init__(self, verbosity: Verbosity):
        self.entries: List[ReportEntry] = []
        self.verbosity = verbosity

    def add(self, entry: ReportEntry):
        self.entries.append(entry)

    def report(self):

        if self.verbosity == Verbosity.none:
            return

        total_files = len(self.entries)
        files_fixed = sum(1 for e in self.entries if e.fixed_cols > 0)

        # 1) Summary
        print("# Column Name Validation Report")
        print(f"- Total files processed: **{total_files}**")
        print(f"- Files fixed: **{files_fixed}**")

        # 2) Table breakdown
        if self.verbosity >= Verbosity.default:
            print("\n## Table Breakdown")
            summary = []
            for e in self.entries:
                summary.append(
                    [
                        e.filename,
                        e.total_cols,
                        e.fixed_cols,
                        ", ".join(e.reasons_summary) or "—",
                    ]
                )
            print(
                tabulate(
                    summary,
                    headers=["File", "Total Cols", "Fixed Cols", "Reasons"],
                    tablefmt="github",
                )
            )

        # 3) Column breakdown
        if self.verbosity >= Verbosity.verbose:
            print("\n## Column Breakdown")
            for e in self.entries:
                print(f"\n### {e.filename}")
                rows = [
                    [c["original"], c["fixed"], ", ".join(c["reasons"]) or "—"]
                    for c in e.column_details
                ]
                print(
                    tabulate(
                        rows,
                        headers=["Original", "Fixed", "Reasons"],
                        tablefmt="github",
                    )
                )


# ----------------------------
# Core Functions
# ----------------------------


def fix_column_name_pipeline(
    col: str, pipeline_config: Optional[Dict[str, bool]] = None
) -> str:
    validator = ColumnNameValidator(pipeline_config)
    return validator.fix(col)


def validate_column_name(
    col: str, pipeline_config: Optional[Dict[str, bool]] = None
) -> Tuple[bool, List[str]]:
    validator = ColumnNameValidator(pipeline_config)
    return validator.validate(col)


def fix_column_names_in_dataframe(
    df: pd.DataFrame, pipeline_config: Optional[Dict[str, bool]] = None
) -> pd.DataFrame:
    new_cols = {c: fix_column_name_pipeline(c, pipeline_config) for c in df.columns}
    return df.rename(columns=new_cols)


def check_true_duplicate_columns(df: pd.DataFrame, fix: bool = False):
    duplicate_groups = []
    seen = set()
    # For every column name that appears more than once
    for col in df.columns[df.columns.duplicated()].unique():
        # Indices of all columns with that name
        idxs = [i for i, c in enumerate(df.columns) if c == col]
        # Compare every pair among those indices
        group = [idxs[0]]  # Keep the first occurrence
        for idx in idxs[1:]:
            # Compare with the first occurrence
            if df.iloc[:, idx].equals(df.iloc[:, group[0]]):
                group.append(idx)
        if len(group) > 1:
            duplicate_groups.append([df.columns[i] for i in group])
            seen.update(group[1:])  # Mark all but the first for removal

    if not fix:
        return duplicate_groups
    else:
        # Drop only the truly duplicate columns (keep first)
        to_drop = [df.columns[i] for group in duplicate_groups for i in group[1:]]
        # For duplicate names, .drop() will drop the *first* occurrence,
        # so we need to drop by index
        cols_to_keep = [i for i in range(len(df.columns)) if i not in seen]
        return df.iloc[:, cols_to_keep]


def validate_columns_in_dataframe(
    df: pd.DataFrame, pipeline_config: Optional[Dict[str, bool]] = None
) -> bool:
    results = [validate_column_name(c, pipeline_config)[0] for c in df.columns]
    return all(results)


def validate_table(
    df: pd.DataFrame,
    *,
    autofix_columns: bool,
    pipeline_config: Optional[Dict[str, bool]] = None,
    save_copy: bool = False,
) -> Tuple[pd.DataFrame, bool, bool]:
    """
    Validates and optionally autofixes a DataFrame.
    Returns (dataframe, valid, modified).
    """
    valid = validate_columns_in_dataframe(df, pipeline_config)
    if valid:
        return df, True, False
    if autofix_columns:
        fixed_df = fix_column_names_in_dataframe(df, pipeline_config)
        return fixed_df, True, True
    return df, False, False


def validate_tables(
    tables: List[pd.DataFrame],
    **options,  # <-- grab *all* the extra flags here
) -> List[Tuple[pd.DataFrame, bool, bool]]:
    """
    Validates a list of DataFrames; returns list of (dataframe, valid, modified).
    Any keyword arguments are passed straight through to `validate_table`.
    """
    results = []
    for df in tables:
        results.append(validate_table(df, **options))
    return results


def _iter_named_tables(
    tables: Iterable[Any],
) -> Iterable[Tuple[str, pd.DataFrame]]:
    table_list = list(tables)

    for idx, item in enumerate(table_list, start=1):
        if isinstance(item, tuple) and len(item) == 2:
            name, df = item
            yield str(name), df
            continue

        name = None
        if hasattr(item, "attrs") and isinstance(item.attrs, dict):
            name = item.attrs.get("name") or item.attrs.get("table_name")

        yield str(name or f"Table_{idx}"), item


def validate_tables_with_reporter(
    tables: List[Any],
    reporter: Reporter,
    autofix_columns: bool,
    pipeline_config: Optional[Dict[str, bool]] = None,
    save_copy: bool = True,
):
    validator = ColumnNameValidator(pipeline_config)
    results = []
    column_mappings: Dict[str, Dict[str, str]] = {}

    for name, df in _iter_named_tables(tables):
        details = []
        for col in df.columns:
            valid, reasons = validator.validate(col)
            fixed = col if valid else validator.fix(col)
            details.append({"original": col, "fixed": fixed, "reasons": reasons})
        reporter.add(ReportEntry(name, details))
        column_mappings[name] = {d["original"]: d["fixed"] for d in details}
        results.append(
            validate_table(
                df=df,
                autofix_columns=autofix_columns,
                pipeline_config=pipeline_config,
                save_copy=save_copy,
            )
        )

    reporter.report()
    return results, column_mappings


def process_and_report_duplicates(
    tables: Iterable[Any],
    *,
    autofix_columns: bool = True,
    pipeline_config: Optional[Dict[str, bool]] = None,
) -> bool:
    """
    For each DataFrame in `tables` (or `(name, df)` tuple), optionally validate/autofix
    columns and report duplicates:
      • Report any duplicated column names (with positions & original names).
      • Print a nicely formatted dict mapping each original name involved in duplicates → ''.
    """
    # 2) Helper to find duplicate column positions in a DataFrame
    def find_duplicate_column_indices(columns: Iterable[Any]) -> Dict[Any, List[int]]:
        col_positions: Dict[Any, List[int]] = defaultdict(list)
        for idx, col in enumerate(columns):
            col_positions[col].append(idx)
        return {col: idxs for col, idxs in col_positions.items() if len(idxs) > 1}

    any_duplicates = False

    # 3) Inspect each table
    for table_id, df in _iter_named_tables(tables):
        original_columns = list(df.columns)
        if autofix_columns:
            df, _, _ = validate_table(
                df=df,
                autofix_columns=True,
                pipeline_config=pipeline_config,
            )

        dup_pos = find_duplicate_column_indices(df.columns)
        duplicates_with_original = defaultdict(list)

        # build mapping dup_name -> list of (index, original_name)
        for dup_name, idx_list in dup_pos.items():
            for idx in idx_list:
                orig_name = original_columns[idx]
                duplicates_with_original[dup_name].append((idx, orig_name))

        # 4a) Print duplicate details
        if len(duplicates_with_original) == 0:
            print(f"No duplicate columns found in table '{table_id}'.")
        else:
            any_duplicates = True
            print(f"Duplicate columns in table '{table_id}':")
            for dup_name, info in duplicates_with_original.items():
                positions = [pos for pos, _ in info]
                originals = [orig for _, orig in info]
                print(
                    f"  • Column '{dup_name}' at positions {positions} "
                    f"(original names: {originals})"
                )

            # 4b) Build & pretty‐print dict of original names → ''
            all_originals = {
                orig for info in duplicates_with_original.values() for _, orig in info
            }
            orig_dict = {orig: "" for orig in sorted(all_originals)}
            print("Original-names dict:")
            print(json.dumps(orig_dict, indent=4, sort_keys=True), end="\n\n")

    return not any_duplicates
