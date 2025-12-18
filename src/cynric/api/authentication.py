from __future__ import annotations

from typing import (
    Dict,
    Optional,
)

from cynric.api.logger import get_logger

log = get_logger(__name__)

# -------------------------------
# Authentication
# -------------------------------


class Auth:
    """Simple Bearer token authentication handler.

    Accepts a static token or a callable for dynamic token retrieval.
    """

    def __init__(self, token: str):
        self.token = token

    def authorization_value(self) -> str:
        token = self.token
        if not token or not isinstance(token, str):
            raise RuntimeError("Auth: token provider returned no valid token.")
        return f"Bearer {token}"

    def headers(
        self,
        method: str,
        url: str,
        content_type: Optional[str] = None,
        hash_content: bool = False,
        include_content_type: bool = False,
        extra: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """Return headers including Authorization and optionally Content-Type."""
        hdrs = {"Authorization": self.authorization_value()}
        if include_content_type and content_type:
            hdrs["Content-Type"] = content_type
        if extra:
            hdrs.update(extra)
        return hdrs
