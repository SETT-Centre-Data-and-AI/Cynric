import pytest  # noqa
import support as support  # noqa
from typing import Any  # noqa


# Helpers
def helper_xxx() -> None:
    pass


# Fixtures
@pytest.fixture(params=[None, "xxx"], ids=["test_none", "test_xxx"])
def arg_name_xxx(request: pytest.FixtureRequest) -> Any:
    return request.param


### ====================== ###
### ---------TESTS---------###
### ====================== ###


def test_template() -> None:  # simple
    pass


def test_with_params(arg_name_xxx) -> None:  # with params
    pass


def test_raises() -> None:  # test raises error
    with pytest.raises(NotImplementedError):
        raise NotImplementedError


# Run
if __name__ == "__main__":
    pytest.main([__file__])
