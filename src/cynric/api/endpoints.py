from __future__ import annotations

import json
import os
from typing import (
    BinaryIO,
    Dict,
    Optional,
    Union,
)

import polars as pl
import requests

from cynric.api.api_client import ApiClient
from cynric.api.integrity import DEFAULT_CHUNK_SIZE, MAX_PAYLOAD_BYTES
from cynric.api.logger import get_logger
from cynric.api.utilities import Utils

log = get_logger(__name__)

# -------------------------------
# Endpoints (resource layer)
# -------------------------------


class Endpoints:
    def __init__(self, api_client: ApiClient, utils: Utils):
        """Initialize with an API client and utility helper."""
        self.api = api_client
        self.utils = utils

    def access_rights(
        self, as_dataframe: bool = False
    ) -> Union[requests.Response, pl.DataFrame]:
        """Fetch dataset access rights."""
        resp = self.api.request("GET", "/datasets/access_rights")
        if not as_dataframe:
            return resp
        try:
            payload = resp.json()
        except ValueError:
            payload = []
        return self.utils.json_to_dataframe(payload)

    def sql_query(
        self,
        sql: str,
        sql_format: str = "query",
        result_as_file: bool = False,
        as_dataframe: bool = False,
    ) -> Union[requests.Response, pl.DataFrame]:
        """Execute a SQL query against the dataset API.

        Accepts raw SQL string or path to a file.
        """
        if sql_format.lower() == "file":
            with open(sql, "r", encoding="utf-8") as f:
                sql_query = f.read()
        elif sql_format.lower() == "query":
            sql_query = sql
        else:
            raise ValueError("Acceptable values for sql_format are 'query' or 'file'")

        payload = json.dumps({"sql": sql_query}, ensure_ascii=False)
        endpoint = "/datasets/queryAsFile" if result_as_file else "/datasets/query"
        # stream to avoid buffering large result files in-memory
        resp = self.api.request(
            "POST", endpoint, data_body=payload, stream=result_as_file
        )

        if not as_dataframe or result_as_file:
            # If result is a file, caller consumes the stream
            return resp
        try:
            data = resp.json()
        except ValueError:
            data = {"rows": []}
        return self.utils.json_to_dataframe(data, element="rows")

    def upload_csv_file(
        self,
        dataset_id: str,
        filepath: str,
        content_type: str = "text/csv",
    ):

        path = f"/datasets/{dataset_id}/upload/CSV_COMMA"

        filename = os.path.basename(filepath)
        files = {"file": (filename, open(filepath, "rb"), content_type)}

        return self.api.request("POST", path, file_body=files)

    def upload_csv_fileobj(
        self,
        dataset_id: str,
        fileobj: BinaryIO,
        filename: str,
        content_type: str = "text/csv",
    ):
        """
        Upload a CSV given an already-open binary file-like object.
        Does not close `fileobj`.
        """
        path = f"/datasets/{dataset_id}/upload/CSV_COMMA"
        files = {"file": (filename, fileobj, content_type)}
        return self.api.request("POST", path, file_body=files)

    def update_dataset(
        self,
        dataset_id: str,
        payload: Union[pl.DataFrame, dict, list, str],
        wrap: bool = True,
        wrap_key: str = "rows",
        null_substitute: Optional[str] = "'null'",
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        max_payload_bytes: int = MAX_PAYLOAD_BYTES,
    ) -> Dict[str, requests.Response]:
        """Upsert rows into a dataset.

        Automatically chunks payload if too large.
        """
        path = f"/datasets/{dataset_id}/rows/upsert"

        # If payload already a JSON string, send as-is
        if isinstance(payload, str):
            resp = self.api.request("POST", path, data_body=payload)
            return {"full": resp}

        records = []

        for record in self.utils.normalize_to_records(payload, drop_missing=True):
            record_dict = {}
            for key, value in record.items():
                if value is not None:
                    record_dict[key] = value
            records.append(record_dict)

        if not records:
            body = self.utils.build_json_payload(
                records, wrap_key=wrap_key, wrap=wrap, null_substitute=null_substitute
            )
            resp = self.api.request("POST", path, data_body=body)
            return {"empty": resp}

        body = self.utils.build_json_payload(
            records, wrap_key=wrap_key, wrap=wrap, null_substitute=null_substitute
        )
        if (
            len(body.encode("utf-8")) <= max_payload_bytes
            and len(records) <= chunk_size
        ):
            resp = self.api.request("POST", path, data_body=body)
            return {"full": resp}

        responses: Dict[str, requests.Response] = {}
        for idx, chunk in enumerate(self.utils.chunk_iterable(records, chunk_size)):
            body = self.utils.build_json_payload(
                chunk, wrap_key=wrap_key, wrap=wrap, null_substitute=null_substitute
            )
            if len(body.encode("utf-8")) > max_payload_bytes:
                # Split further by halving the chunk size (iterative generator)
                sub_chunks = list(
                    self.utils.chunk_iterable_iter(chunk, max(1, chunk_size // 2))
                )
                if len(sub_chunks) == 1:
                    raise ValueError(
                        "Chunk size results in payload larger than max_payload_bytes; reduce chunk_size."
                    )
                for sub_idx, s_chunk in enumerate(sub_chunks):
                    s_body = self.utils.build_json_payload(
                        s_chunk,
                        wrap_key=wrap_key,
                        wrap=wrap,
                        null_substitute=null_substitute,
                    )
                    if len(s_body.encode("utf-8")) > max_payload_bytes:
                        raise ValueError(
                            "Even sub-chunk exceeds max_payload_bytes; reduce chunk size or record size."
                        )
                    responses[f"chunk:{idx}.{sub_idx}"] = self.api.request(
                        "POST",
                        path,
                        data_body=s_body,
                        headers={"Content-Type": "application/json"},
                    )
            else:
                responses[f"chunk:{idx}"] = self.api.request(
                    "POST",
                    path,
                    data_body=body,
                    headers={"Content-Type": "application/json"},
                )

        return responses

    def get_dataset(
        self, dataset_id: str, as_dataframe: bool = False
    ) -> Union[requests.Response, pl.DataFrame]:
        """Fetch dataset by ID (metadata or rows depending on API).

        This default assumes /datasets/{id} returns metadata or { "rows": [...] }.
        If your API exposes rows at /datasets/{id}/rows, update the path below.
        """
        resp = self.api.request("GET", f"/datasets/{dataset_id}/rows")
        if not as_dataframe:
            return resp
        try:
            payload = resp.json()
        except ValueError:
            payload = {}
        # If the payload is { "rows": [...] } use that, else convert whole dict
        if (
            isinstance(payload, dict)
            and "rows" in payload
            and isinstance(payload["rows"], list)
        ):
            return self.utils.json_to_dataframe(payload, element="rows")

        if not payload:
            return pl.DataFrame()

        return self.utils.json_to_dataframe(payload)

    def get_datasets_list(self):
        resp = self.api.request("GET", "/datasets")
        return resp

    def get_dataset_form(
        self, dataset_id: str, as_dataframe: bool = False
    ) -> Union[requests.Response, pl.DataFrame]:
        """Fetch the form definition for a dataset."""
        resp = self.api.request("GET", f"/datasets/{dataset_id}/form")
        if not as_dataframe:
            return resp
        try:
            payload = resp.json()
        except ValueError:
            payload = {}
        return self.utils.json_to_dataframe(payload)

    def get_form_columns(
        self,
        dataset_id: str,
        as_dataframe: bool = False,
    ) -> Union[requests.Response, pl.DataFrame]:
        """Fetch column definitions for a form.

        Can infer form_id from dataset_id.
        """

        resp = self.api.request("GET", f"/datasets/{dataset_id}/formandcolumns")

        if not as_dataframe:
            return resp
        try:
            payload = resp.json()
        except ValueError:
            payload = {}
        return self.utils.json_to_dataframe(payload, element="columns")

    def decode_df_choices(
        self,
        df: pl.DataFrame,
        dsid: str,
        *,
        mode: str = "replace",  # 'replace' | 'append' -> append *_LABEL columns
        label_suffix: str = "_LABEL",
    ) -> pl.DataFrame:
        """Decode choice-coded columns for dsid using BCPlatforms form metadata.

        - mode='replace': overwrite original columns with labels (default)
        - mode='append': add <col>_LABEL columns with labels, keep originals
        """
        log = get_logger(__name__)
        try:

            cols_df = self.get_form_columns(dsid, as_dataframe=True)
            decode_dict = self.utils.extract_choices(cols_df)  # type: ignore

            # no choice-coded columns -> return df as-is
            if not decode_dict:
                return df

            out = df
            for column, mapping in decode_dict.items():
                if column not in out.columns or not mapping:
                    continue

                # Robust map preserving unknown values
                mapper = self.utils._map_with_preserve(mapping)
                mapped_expr = (
                    pl.col(column)
                    .cast(pl.Utf8)
                    .map_elements(mapper, return_dtype=pl.Utf8)
                )

                if mode == "append":
                    out = out.with_columns(mapped_expr.alias(f"{column}{label_suffix}"))
                else:
                    out = out.with_columns(mapped_expr.alias(column))

            return out
        except Exception as e:
            log.warning(f"decode_choices: failed for {dsid}: {e}")
            return df

    def get_job_status(self, submission_id: str) -> Optional[str]:
        """Query the API for the latest status of a submission."""
        path = f"/datasets/job/status/{submission_id}"
        try:
            resp = self.api.request("GET", path)
            status = resp.json()
        except Exception as exc:
            log.warning("Unable to fetch status for %s: %s", submission_id, exc)
            return None

        return status
