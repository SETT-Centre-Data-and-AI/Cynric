from valediction.integrity import inject_config_variables

CYNRIC_VARIABLES = {
    "allow_bigint": False,
    "pk_col_max_length": 64,
    "enforce_no_null_columns": False,
}


def inject_cynric_variables() -> None:
    inject_config_variables(CYNRIC_VARIABLES)
