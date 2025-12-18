from __future__ import annotations

import json
import threading
import urllib.request
import warnings
from importlib.metadata import version as installed_version

_checked_once = False
_lock = threading.Lock()


class CynricUpdateAvailableWarning(UserWarning):
    """Raised when a newer Cynric version is available on PyPI."""


def _is_newer(latest: str, current: str) -> bool:
    """Best-effort version compare (handles semver if packaging is available)."""
    try:
        from packaging.version import Version  # optional dependency

        return Version(latest) > Version(current)
    except Exception:
        return latest != current


def check_version(
    *,
    package: str = "cynric",
    timeout_s: float = 5,
) -> None:
    """Check PyPI for a newer version of `package`.

    - Fires once per Python process
    - Returns immediately (runs in daemon thread)
    - Short timeout
    - Fails silently (no internet, PyPI blocked, etc.)
    - Emits a warning if a newer version exists
    """
    global _checked_once
    with _lock:
        if _checked_once:
            return
        _checked_once = True

    def _worker() -> None:
        try:
            current = installed_version(package)

            url = f"https://pypi.org/pypi/{package}/json"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": f"{package} version check"},
            )
            with urllib.request.urlopen(req, timeout=timeout_s) as r:
                data = json.loads(r.read().decode("utf-8"))
            latest = data.get("info", {}).get("version")
            if not latest:
                return

            if _is_newer(str(latest), str(current)):
                cmd = "python -m pip install -U cynric"
                warnings.warn(
                    "New version of Cynric available. "
                    "To remain aligned with Wessex SDE updates, please update using pip "
                    f"with `{cmd}`, or your preferred package manager.",
                    category=CynricUpdateAvailableWarning,
                    stacklevel=2,
                )
        except Exception:
            pass  # silent failure by design

    threading.Thread(target=_worker, daemon=True).start()
