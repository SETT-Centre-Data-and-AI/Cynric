from valediction.integrity import inject_config_variables

CYNRIC_VARIABLES = {"allow_bigint": False}  # TODO: wire bigint checks into Valediction


def inject_cynric_variables() -> None:
    inject_config_variables(CYNRIC_VARIABLES)
