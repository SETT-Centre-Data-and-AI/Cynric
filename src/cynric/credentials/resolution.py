from __future__ import annotations

from cynric.credentials.credentials import get_base_url, get_token
from cynric.credentials.helpers import validate_token, validate_url
from cynric.exceptions import CredentialNotSaved


def resolve_credentials(*, token: str | None = None, base_url: str | None = None) -> tuple[str, str]:
    """Resolve and validate credentials.

    If ``token``/``base_url`` are provided, they are validated. Missing values are
    fetched from OS credential storage (if previously saved with
    ``cynric.save_credentials()``).

    Args:
        token: Authentication token for the Wessex SDE API, or ``None``/empty to
            fetch from OS credential storage.
        base_url: Base URL for the Wessex SDE API, or ``None``/empty to fetch
            from OS credential storage.

    Returns:
        A tuple of ``(base_url, token)``.

    Raises:
        CredentialNotSaved: If any required credential is missing and could not
            be fetched from OS credential storage.
        InvalidUrlError: If the provided/fetched ``base_url`` is invalid.
        InvalidTokenError: If the provided/fetched ``token`` is invalid.
        ExpiredTokenError: If the provided/fetched ``token`` is expired.
    """
    token = token or ""
    base_url = base_url or ""

    if base_url:
        base_url = validate_url(base_url)
    if token:
        token = validate_token(token)

    if not base_url:
        try:
            base_url = get_base_url()
        except CredentialNotSaved as e:
            raise CredentialNotSaved(
                "No `base_url` provided, and could not fetch from OS credential storage. "
                "Please pass in a `base_url` argument, or save credentials with "
                "`cynric.save_credentials()`"
            ) from e

    if not token:
        try:
            token = get_token()
        except CredentialNotSaved as e:
            raise CredentialNotSaved(
                "No `token` provided, and could not fetch from OS credential storage. "
                "Please pass in a `token` argument, or save credentials with "
                "`cynric.save_credentials()`"
            ) from e

    return base_url, token

