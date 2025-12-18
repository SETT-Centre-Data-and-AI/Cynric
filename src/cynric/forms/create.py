from typing import Dict
import warnings

try:
    import pandas as pd
except ModuleNotFoundError as exc:  # pragma: no cover
    raise ModuleNotFoundError(
        "cynric.forms requires `pandas` (and typically `openpyxl` for exports). "
        "Install with `pip install pandas openpyxl`."
    ) from exc
from pathlib import Path


def create_choiceset_df(df, choice_cols, table):

    table_name = table.name
    choiceset_options = table.choiceset_options

    if len(choice_cols) == 0:
        choices_df = None
        column_choicesets = pd.DataFrame(
            columns=["Table", "Column", "Choiceset", "Choiceset Index"]
        )

        return choices_df, column_choicesets

    choices = []
    all_processed_choicesets = []

    if isinstance(choiceset_options, Dict):
        for col in choiceset_options:
            unique_values = df[col].dropna().drop_duplicates().tolist()
            choiceset_values = choiceset_options[col]
            if choiceset_values == "auto":
                unique_values = unique_values
            else:
                missing = set(choiceset_values) - set(unique_values)
                if missing:
                    warnings.warn(
                        f"choiceset_values, {choiceset_values} are missing from the dataset {table_name}",
                        UserWarning,
                        stacklevel=2,
                    )

                unique_values = choiceset_values

            _append_choice(choices, col, unique_values)

    elif choiceset_options == "auto":
        for col in choice_cols:
            unique_values = df[col].dropna().drop_duplicates().tolist()
            _append_choice(choices, col, unique_values)

    choices_df = pd.concat(choices)
    grouped_choicesets = choices_df.groupby("Column")

    for idx, (col, col_choiceset) in enumerate(grouped_choicesets):

        col_choiceset["string"] = (
            col_choiceset["Number"].astype(str) + "=" + col_choiceset["Value"]
        )

        line = str(idx)
        for item in col_choiceset["string"]:
            line += f"\t{item}"

        processed = (table_name, col, line, idx)
        all_processed_choicesets.append(processed)

    column_choicesets = pd.DataFrame(
        all_processed_choicesets,
        columns=["Table", "Column", "Choiceset", "Choiceset Index"],
    )

    column_choicesets["Choiceset Index"] = column_choicesets["Choiceset Index"].astype(
        "Int64"
    )

    return choices_df, column_choicesets


def _append_choice(choices, col, unique_values):
    choices.append(
        pd.DataFrame(
            {
                "Column": col,
                "Number": list(range(len(unique_values))),
                "Value": unique_values,
            }
        )
    )


def create_header_footer(name):
    return f"<{name}>", f"</{name}>"


def create_form_properties(name):
    header, footer = create_header_footer("properties")

    properties = {
        "name": name,
        "family": "PHENOTYPES",
        "databaseFormCharset": "ISO-8859-15",
        "dbVersion": "3.0",
        "formFileCharset": "ISO-8859-15",
        "origin": "created_with_v3_editor",
        "version": "3.0",
    }

    body = "\n".join(f"{key}={value}" for key, value in properties.items())

    return f"{header}\n{body}\n{footer}"


def create_form_description(table_details, table_name):
    header, footer = create_header_footer("description")

    table = table_details[table_details["Table"] == table_name]
    body = table["Description"].iloc[0]

    return f"{header}\n{body}\n{footer}"


def create_form_choicesets(column_details, table_name):

    header, footer = create_header_footer("choicesets")

    table_choicesets = column_details[(column_details["Choiceset"].notna())]

    choiceset_list = table_choicesets["Choiceset"].astype(str)
    body = "\n".join(choiceset_list)

    return f"{header}\n{body}\n{footer}"


def create_form_variables(column_details, table_name):

    header, footer = create_header_footer("variables")

    variable_items = [
        "VARIABLE",
        "DESCRIPTION",
        "TYPE",
        "KEY",
        "MINVAL",
        "MAXVAL",
        "CHOICESET",
        "REQUIRED",
        "LENGTH",
        "VALUEFUNCTION",
        "DEFAULT",
        "VALUEFORMATREGEXP",
        "BCDBITRATE",
    ]

    mapping = {
        "Column": "VARIABLE",
        "Column Description": "DESCRIPTION",
        "Data Type": "TYPE",
        "Key": "KEY",
        "Choiceset Index": "CHOICESET",
        "Length": "LENGTH",
    }

    # table_column_details = column_details[column_details["Table"] == table_name]
    table_column_details = column_details

    variable_df = table_column_details.rename(columns=mapping)

    for item in variable_items:
        if item not in variable_df.columns:
            variable_df[item] = [""] * variable_df.shape[0]

    for col in variable_df:
        if col not in variable_items:
            variable_df = variable_df.drop(col, axis=1)

    variable_df = variable_df[variable_items]

    body = variable_df.to_csv(sep="\t", index=False).rstrip("\n")

    # variable_df.columns = variable_items
    return f"{header}\n{body}\n{footer}"


def create_form_columnannotations(annotations):
    columnannotations_items = [
        "VARIABLE",
        "ONTOLOGY_ID",
        "TERM_ID",
        "RELATIONSHIP_TYPE",
    ]

    header, footer = create_header_footer("columnannotations")
    body = "\t".join(columnannotations_items)

    return f"{header}\n{body}\n{footer}"


def create_form(
    form_name: str,
    table_details: pd.DataFrame,
    column_details: pd.DataFrame,
    table_name: str,
    output_dir: Path | str | None = None,
):
    """
    Docstring for create_form

    form_name
    table_details: Pandas dataframe ['Table', 'Description']
    column_details: Pandas dataframe ['Column', 'Data Type', 'Key', 'Length', 'Column Description', 'Table',
       'Choiceset', 'Choiceset Index']
    """

    form = "\n".join(
        [
            create_form_properties(name=form_name),
            create_form_description(table_details=table_details, table_name=table_name),
            create_form_choicesets(
                column_details=column_details, table_name=table_name
            ),
            create_form_variables(column_details=column_details, table_name=table_name),
            # create_form_columnannotations(annotations=annotations)
        ]
    )

    if output_dir is not None:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        filepath = output_path / f"{table_name}.txt"
        with open(filepath, "w") as f:
            f.write(form)

    return form
