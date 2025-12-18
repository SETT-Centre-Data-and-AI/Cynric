import base64
import binascii
import json
import time
from urllib.parse import urlparse

from cynric.exceptions import ExpiredTokenError, InvalidTokenError, InvalidUrlError


def _b64url_decode(segment: str) -> bytes:
    padding = "=" * (-len(segment) % 4)  # add padding
    return base64.urlsafe_b64decode(segment + padding)


def validate_url(url: str) -> str:
    """Check URL is valid."""
    error_message = "Invalid Wessex SDE API URL provided. Please check."
    if not isinstance(url, str):
        raise InvalidUrlError(error_message)

    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise InvalidUrlError(error_message)

    if not parsed.netloc:
        raise InvalidUrlError(error_message)

    if " " in url:
        raise InvalidUrlError(error_message)

    return url


def validate_token(token: str) -> str:
    """Validates JWT integrity & expiry.

    Does not check the signature.
    """

    error_message = "Invalid token. Please contact the Wessex SDE."
    error_message_expired = "Token has expired. Please contact the Wessex SDE."

    if not isinstance(token, str):
        raise InvalidTokenError("Token must be a string")

    token = token.strip()
    if not token:
        raise InvalidTokenError("Token must not be empty")

    parts = token.split(".")
    if len(parts) != 3:
        raise InvalidTokenError(
            "Invalid token format - must have three parts"
        ) from None

    header_b64, payload_b64, _signature_b64 = parts

    # Check decode
    try:
        header_bytes = _b64url_decode(header_b64)
        payload_bytes = _b64url_decode(payload_b64)
    except (binascii.Error, ValueError):
        raise InvalidTokenError(error_message) from None

    # Parse JSON
    try:
        _header = json.loads(header_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise InvalidTokenError(error_message) from None

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise InvalidTokenError(error_message) from None

    # Check exp
    if "exp" not in payload:
        raise InvalidTokenError(error_message) from None

    try:
        exp = int(payload["exp"])
    except (ValueError, TypeError):
        raise InvalidTokenError(error_message) from None

    now = int(time.time())
    if exp <= now:
        raise ExpiredTokenError(error_message_expired) from None

    return token
