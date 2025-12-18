from __future__ import annotations

from typing import Any  # noqa

from cynric.api.logger import get_logger

log = get_logger(__name__)

# -------------------------------
# Constants / Defaults
# -------------------------------

# Uploading
DEFAULT_CHUNK_SIZE = (
    10_000  # records per chunk for upserts (tune to payload size limits)
)
MAX_PAYLOAD_BYTES = 50 * 1024 * 1024  # 50MB (server-dependent)

USER_AGENT = "bcplatforms-python-client/1.0"

# Expanded common sensitive names for safer logging
SENSITIVE_HEADERS = {
    "authorization",
    "cookie",
    "set-cookie",
    "x-api-key",
    "x-auth-token",
    "proxy-authorization",
}
SECRET_PARAMS = {
    "access_token",
    "token",
    "apikey",
    "api_key",
    "authorization",
    "sig",
    "signature",
}
