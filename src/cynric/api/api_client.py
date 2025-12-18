from __future__ import annotations

from typing import (
    Any,
    Dict,
    Optional,
    Union,
)
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from cynric.api.integrity import SECRET_PARAMS, SENSITIVE_HEADERS, USER_AGENT
from cynric.api.logger import get_logger

log = get_logger(__name__)

# -------------------------------
# Low-level HTTP client
# -------------------------------


class ApiClient:
    def __init__(
        self,
        base_url: str,
        signer: Any,
        timeout: float = 30.0,
        max_retries: int = 3,
        backoff_factor: float = 0.5,
        pool_connections: int = 20,
        pool_maxsize: int = 20,
        verify: Union[bool, str] = True,
        proxies: Optional[Dict[str, str]] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.signer = signer
        self.timeout = timeout
        self.logger = get_logger(__name__)
        self.session = requests.Session()
        self.session.verify = verify
        if proxies:
            self.session.proxies.update(proxies)

        # Default headers
        self.session.headers.update(
            {
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            }
        )

        # Retry strategy
        retry = Retry(
            total=max_retries,
            connect=max_retries,
            read=max_retries,
            status=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset(
                ["GET", "HEAD", "OPTIONS", "PUT", "DELETE", "TRACE", "POST", "PATCH"]
            ),
            respect_retry_after_header=True,
        )

        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=pool_connections,
            pool_maxsize=pool_maxsize,
        )

        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def build_url(self, path_or_url: str) -> str:
        """Build a full URL from a relative path or return absolute URL as-is."""
        return (
            path_or_url
            if self.is_abs_url(path_or_url)
            else self.safe_join(self.base_url, path_or_url)
        )

    def request(
        self,
        method: str,
        path_or_url: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Union[Dict[str, Any], list]] = None,
        data_body: Optional[Union[str, bytes]] = None,
        file_body: Optional[Union[str, bytes]] = None,
        headers: Optional[Dict[str, str]] = None,
        content_type: Optional[str] = "application/json",
        timeout: Optional[float] = None,
        stream: bool = False,
        hash_content: bool = False,
    ) -> requests.Response:
        """Make a signed HTTP request with retry and timeout support."""
        url = self.build_url(path_or_url)
        method = method.upper()

        # Prepare headers
        hdrs = dict(headers or {})
        # Explicit Content-Type when sending data directly (not json=)
        if content_type and "Content-Type" not in hdrs:  # and data_body is not None:
            hdrs["accept"] = content_type

        # Add auth headers
        auth_header = self.signer.headers(
            method=method,
            url=url,
            content_type=content_type,  # or ""
            hash_content=hash_content,
        )
        hdrs.update(auth_header)

        # Log request (mask secrets)
        safe_headers = self.redact_headers(hdrs)
        self.logger.debug(
            "Request: [%s %s] params=%s headers=%s",
            method,
            self.mask_url_query(url),
            params,
            safe_headers,
        )

        try:
            # Send request
            resp = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_body if json_body is not None else None,
                data=data_body if json_body is None else None,
                files=file_body if file_body is not None else None,  # type: ignore
                headers=hdrs,  # type: ignore
                timeout=timeout or self.timeout,
                stream=stream,
            )
        except requests.exceptions.RequestException as exc:
            # Network/timeout/connection errors
            self.logger.error(
                "Request failed: [%s %s] %r", method, self.mask_url_query(url), exc
            )
            raise

        self.logger.debug(
            "Response: [%s %s] status=%s",
            method,
            self.mask_url_query(url),
            resp.status_code,
        )

        # Raise error if not OK
        if not resp.ok:
            msg = f"{method} {url} ->"
            # Try JSON body, fallback to text (trim)
            try:
                detail = resp.json()
            except Exception:
                detail = (resp.text or "")[:1000]

            code = resp.status_code
            if code in (401, 403):
                error = f"AUTH ERROR ({code})"
            elif code == 404:
                error = f"NOT FOUND ERROR ({code})"
            elif 400 <= code < 500:
                error = f"CLIENT ERROR ({code})"
            elif code >= 500:
                error = f"SERVER ERROR ({code})"
            else:
                error = f"OTHER ERROR ({code})"

            self.logger.warning("HTTP error: %s detail=%s", error, str(detail)[:1000])
            raise RuntimeError(f"{msg} {error}: {detail}")

        return resp

    @staticmethod
    def safe_join(base: str, path: str) -> str:
        base = base.rstrip("/") + "/"
        path = path.lstrip("/")
        return urljoin(base, path)

    @staticmethod
    def is_abs_url(url: str) -> bool:
        return url.startswith("http://") or url.startswith("https://")

    @staticmethod
    def redact_headers(headers: Dict[str, str]) -> Dict[str, str]:
        return {
            k: "<redacted>" if k.lower() in SENSITIVE_HEADERS else v
            for k, v in (headers or {}).items()
        }

    @staticmethod
    def mask_url_query(url: str) -> str:
        """Redact known secret query parameters from URLs for safe logging."""
        try:
            parts = urlsplit(url)
            if not parts.query:
                return url
            q = parse_qsl(parts.query, keep_blank_values=True)
            masked = [
                (k, "<redacted>") if k.lower() in SECRET_PARAMS else (k, v)
                for (k, v) in q
            ]
            return urlunsplit(parts._replace(query=urlencode(masked)))
        except Exception:
            return url

    def close(self):
        """Close the underlying session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
