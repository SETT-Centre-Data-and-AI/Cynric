import pytest  # noqa
import support as support  # noqa
from typing import Any  # noqa
import importlib

TEST_INJECTION = "INJECTION_TEST"


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


def test_valediction_injection_starts_empty() -> None:
    from valediction.integrity import Config

    config = Config()

    with pytest.raises(AttributeError):
        getattr(config, TEST_INJECTION)


def test_valediction_injection_success(_restore_cynric_variables) -> None:
    from valediction.integrity import Config

    from cynric.instantiation import CYNRIC_VARIABLES, inject_cynric_variables

    CYNRIC_VARIABLES[TEST_INJECTION] = True
    inject_cynric_variables()

    with Config() as config:
        assert getattr(config, TEST_INJECTION) is True


def test_cynric_injection(_restore_cynric_variables) -> None:
    """Cynric should be able to inject its variables into Valediction."""
    from valediction.integrity import Config

    from cynric.instantiation import CYNRIC_VARIABLES, inject_cynric_variables

    inject_cynric_variables()

    with Config() as config:
        for key, value in CYNRIC_VARIABLES.items():
            assert getattr(config, key) == value


def test_cynric_injection_enforces_no_null_columns(_restore_cynric_variables) -> None:
    from valediction import get_config

    from cynric.instantiation import inject_cynric_variables

    inject_cynric_variables()

    assert get_config().enforce_no_null_columns is False


def test_importing_cynric_triggers_injection(_restore_cynric_variables) -> None:
    import cynric
    from cynric.instantiation import CYNRIC_VARIABLES

    importlib.reload(cynric)

    from valediction.integrity import Config

    cfg = Config()
    for k, v in CYNRIC_VARIABLES.items():
        assert getattr(cfg, k) == v


# Run
if __name__ == "__main__":
    pytest.main([__file__])
