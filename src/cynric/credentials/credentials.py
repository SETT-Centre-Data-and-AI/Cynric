import keyring
from keyring.errors import PasswordDeleteError

from cynric.credentials.helpers import validate_token, validate_url
from cynric.exceptions import CredentialNotSaved

CYNRIC = "CYNRIC"
TOKEN = "TOKEN"
BASE_URL = "BASE_URL"


def _save(element: str, secret: str) -> None:
    "Save secret to OS backend (element@CYNRIC)"
    keyring.set_password(service_name=CYNRIC, username=element, password=secret)


def _get(element: str) -> str:
    """Retrieve secret from OS backend (element@CYNRIC)"""
    secret = keyring.get_password(service_name=CYNRIC, username=element)
    if not secret:
        raise CredentialNotSaved(
            f"Secret for {element} has not been saved in OS credential storage. "
            "Please save credentials with `cynric.save_credentials()`"
        )
    return secret


def _delete(element: str) -> None:
    """Delete secret from OS backend (element@CYNRIC)"""
    try:
        keyring.delete_password(service_name=CYNRIC, username=element)
    except PasswordDeleteError as e:
        # Check deleted
        try:
            _get(element)
            raise PasswordDeleteError from e
        except CredentialNotSaved:
            return


def save_credentials(base_url: str, token: str) -> None:
    """Saves base API URL and secret token to OS credential storage. This allows scripts
    to be run without storing credentials within the code base. Secrets are validated
    before saving. These credentials can be provided by the Wessex SDE team.

    NOTE: Saving credentials on a shared login allows other users
    with access to extract the secrets.

    Args:
        base_url (str): API URL endpoint for the Wessex SDE.
        token (str): Secret user-specific token
    """
    base_url = validate_url(base_url)
    token = validate_token(token)

    _save(BASE_URL, base_url)
    _save(TOKEN, token)


def delete_credentials() -> None:
    _delete(BASE_URL)
    _delete(TOKEN)


def get_base_url() -> str:
    url = _get(BASE_URL)
    return validate_url(url)


def get_token() -> str:
    token = _get(TOKEN)
    return validate_token(token)
