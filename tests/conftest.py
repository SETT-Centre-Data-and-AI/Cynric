import os
import warnings
from pathlib import Path

import pytest
from dotenv import load_dotenv

root = Path(__file__).resolve().parent.parent
load_dotenv(root / ".env")


def pytest_collection_modifyitems(config, items):
    missing_credentials = not os.getenv("BC_TOKEN") or not os.getenv("DEFAULT_BASE_URL")
    running_in_github_actions = os.getenv("GITHUB_ACTIONS", "").lower() == "true"

    if not (missing_credentials or running_in_github_actions):
        return

    reason = "Internal tests require local credentials and are skipped in CI."
    skip_internal = pytest.mark.skip(reason=reason)

    for item in items:
        if "internal" in item.keywords:
            item.add_marker(skip_internal)


def pytest_configure():
    for key in ("BC_TOKEN", "DEFAULT_BASE_URL"):
        if not os.getenv(key):
            warnings.warn(f"Missing optional env var: {key}", stacklevel=1)
