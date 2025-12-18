from __future__ import annotations

import ast
import json
import math
import re
from pathlib import Path
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

import polars as pl

from .logger import get_logger

log = get_logger(__name__)

T = TypeVar("T")


# -------------------------------
# Utilities
# -------------------------------
class Utils:

    def json_to_dataframe(
        self, payload: Any, element: Optional[str] = None
    ) -> pl.DataFrame:
        """Convert a JSON-like payload to a Polars DataFrame.

        If `element` is specified and `payload` is a dict, extract that element.
        """
        data = (
            payload.get(element, [])
            if element and isinstance(payload, dict)
            else payload
        )
        if data is None:
            data = []
        records = [data] if isinstance(data, dict) else data

        if not records:
            return pl.DataFrame()  # Return empty DataFrame explicitly
        return pl.from_dicts(list(records))

    def normalize_to_records(
        self, data: Union[pl.DataFrame, Dict, List], drop_missing: bool = False
    ) -> List[Dict]:
        """Normalize input data to a list of dictionaries (records).

        Supports Polars DataFrame, dict, or list of dicts/scalars.
        """
        if isinstance(data, pl.DataFrame):
            return data.to_dicts()
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            if not data:
                return []
            if all(isinstance(x, dict) for x in data):
                return data
            # List of scalars → wrap into a dict field called 'value'
            records = [{"value": x} for x in data]

            if drop_missing:
                records = [
                    {k: v for k, v in r.items() if v is not None} for r in records
                ]

            return records

        raise TypeError(f"Unsupported payload type: {type(data)}")

    def _is_null_like(self, x: Any) -> bool:
        """Determine if a value is null-like (None or NaN)."""
        if x is None:
            return True
        if isinstance(x, float) and math.isnan(x):
            return True
        return False

    def _replace_none(self, obj: Any, null_substitute: Optional[str]) -> Any:
        """Recursively replace None/NaN values with a substitute string or leave as real
        JSON nulls."""
        if self._is_null_like(obj):
            return None if null_substitute is None else null_substitute
        if isinstance(obj, list):
            return [self._replace_none(x, null_substitute) for x in obj]
        if isinstance(obj, tuple):
            return tuple(self._replace_none(list(obj), null_substitute))
        if isinstance(obj, dict):
            return {k: self._replace_none(v, null_substitute) for k, v in obj.items()}
        return obj

    def build_json_payload(
        self,
        data: Union[pl.DataFrame, Dict, List],
        wrap_key: str = "rows",
        wrap: bool = True,
        null_substitute: Optional[str] = "NA",
    ) -> str:
        """Build a JSON string from input data, optionally wrapping it under a key.

        Nulls can be replaced with a substitute string or left as JSON nulls.
        """
        records = self.normalize_to_records(data)
        records = self._replace_none(records, null_substitute)
        obj = {wrap_key: records} if wrap else records
        return json.dumps(obj, ensure_ascii=False, allow_nan=False)

    def chunk_iterable(self, items: Sequence[T], chunk_size: int) -> Iterator[List[T]]:
        for i in range(0, len(items), chunk_size):
            yield list(items[i : i + chunk_size])

    def chunk_iterable_iter(
        self, items: Iterable[T], chunk_size: int
    ) -> Iterator[List[T]]:
        """Chunk arbitrary iterables (not only sequences)."""
        chunk: List[T] = []
        for x in items:
            chunk.append(x)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        if chunk:
            yield chunk

    def extract_choices(self, form_cols: pl.DataFrame) -> dict[str, dict[str, str]]:
        """
        Build a mapping:
        { <column_id>: { <encoded_value>: <decoded_label>, ... }, ... }

        Expects case-insensitive columns: 'id' and 'choices'
        - 'choices' is a list[str] like "1 = 'Male'".
        """
        cols = {c.lower(): c for c in form_cols.columns}
        if "id" not in cols or "choices" not in cols:
            raise KeyError(
                f"extract_choices: expected columns ['id','choices'], got {form_cols.columns}"
            )

        id_col, choices_col = cols["id"], cols["choices"]
        form_cols = form_cols.select(
            [pl.col(id_col).alias("id"), pl.col(choices_col).alias("choices")]
        )

        decode_dict: dict[str, dict[str, str]] = {}
        for col_id, choices in form_cols.iter_rows():
            if not choices:
                continue
            parsed: dict[str, str] = {}
            for choice in choices:
                if "=" in choice:
                    # allow "idx= 'label'" or "idx = 'label'"
                    idx, val = choice.split("=", 1)
                    parsed[idx.strip()] = val.strip().strip("'").strip('"')
            if parsed:
                decode_dict[col_id] = parsed
        return decode_dict

    def _map_with_preserve(
        self, mapping: dict[str, str]
    ) -> Callable[[str | None], str | None]:
        """Returns a function suitable for pl.map_elements that replaces only known keys
        and preserves others."""

        def _fn(v: str | None) -> str | None:
            if v is None:
                return None
            return mapping.get(str(v), str(v))

        return _fn