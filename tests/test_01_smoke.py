import pytest  # noqa
import support as support  # noqa
from typing import Any  # noqa

### ====================== ###
### ---------TESTS---------###
### ====================== ###


# API
def test_import_integrity() -> None:
    from cynric.api import integrity  # noqa


def test_import_logger() -> None:
    from cynric.api.logger import get_logger  # noqa


def test_import_authentication() -> None:
    from cynric.api import authentication  # noqa


def test_import_api_client() -> None:
    from cynric.api import api_client  # noqa


def test_import_utilities() -> None:
    from cynric.api import utilities  # noqa


def test_import_endpoints() -> None:
    from cynric.api import endpoints  # noqa


def test_import_bc() -> None:
    from cynric.api import bc  # noqa


def test_import_queue() -> None:
    from cynric.api import queue  # noqa


# Dataset Manager
def test_import_mapper() -> None:
    from cynric.dataset_manager import mapper  # noqa


def test_import_navigator() -> None:
    pass  #


# Credentials
def test_import_credentials_helpers() -> None:
    from cynric.credentials import helpers  # noqa


def test_import_credentials() -> None:
    from cynric.credentials import credentials  # noqa


# Uploading
def test_import_uploading() -> None:
    from cynric.uploading import uploading  # noqa


def test_import_uploading_helpers() -> None:
    from cynric.uploading import helpers  # noqa


# Forms
# empty


# Full
def test_import_cynric() -> None:
    import cynric  # noqa


# Run
if __name__ == "__main__":
    pytest.main([__file__])
    """Test that the test raises an error."""
