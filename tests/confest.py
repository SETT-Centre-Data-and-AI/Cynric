# tests/conftest.py
import os
import warnings
from pathlib import Path
from dotenv import load_dotenv

root = Path(__file__).resolve().parent.parent
load_dotenv(root / ".env")


def pytest_configure():
    for key in ("BC_TOKEN", "DEFAULT_BASE_URL"):
        if not os.getenv(key):
            warnings.warn(f"Missing optional env var: {key}")
