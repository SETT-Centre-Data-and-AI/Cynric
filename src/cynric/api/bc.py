from __future__ import annotations

from logging import Logger
from pathlib import Path
from typing import (
    BinaryIO,
    Dict,
    Optional,
    Union,
)

import polars as pl

from cynric.api.api_client import ApiClient
from cynric.api.authentication import Auth
from cynric.api.endpoints import Endpoints
from cynric.api.logger import get_logger
from cynric.api.utilities import Utils

log = get_logger(__name__)


# -------------------------------
# High-level Client
# -------------------------------


class BCPlatforms:
    """High-level client that composes resource classes and exposes backward-compatible
    convenience methods."""

    def __init__(
        self,
        token: str,
        base_url: str,
        timeout: float = 30.0,
        verify: Union[bool, str] = True,
        proxies: Optional[Dict[str, str]] = None,
    ):
        self.signer = Auth(token=token)
        self.api = ApiClient(
            base_url=base_url,
            signer=self.signer,
            timeout=timeout,
            verify=verify,
            proxies=proxies,
        )
        self.utils = Utils()
        self.endpoints = Endpoints(self.api, self.utils)
        self.logger: Logger = log

    # ---------- Explicit connectivity check ----------
    def check_connection(self) -> bool:
        self.logger.debug("Checking connection to datasets/access_rights")
        resp = self.api.request("GET", "/datasets/access_rights")
        ok = resp.status_code == 200
        self.logger.debug("Connection check status=%s", resp.status_code)
        return ok

    # ---------- Public methods (wrapping resources) ----------
    def access_rights(self, as_dataframe: bool = False):
        return self.endpoints.access_rights(as_dataframe=as_dataframe)

    def get_dataset(self, dataset_id: str, as_dataframe: bool = False):
        return self.endpoints.get_dataset(dataset_id, as_dataframe=as_dataframe)

    def get_datasets_list(self):
        return self.endpoints.get_datasets_list()

    def sql_query(
        self,
        sql: str,
        sql_format: str = "query",
        as_dataframe: bool = False,
        result_as_file: bool = False,
    ):
        return self.endpoints.sql_query(
            sql,
            sql_format=sql_format,
            as_dataframe=as_dataframe,
            result_as_file=result_as_file,
        )

    def get_dataset_form(self, dataset_id: str, as_dataframe: bool = False):
        return self.endpoints.get_dataset_form(dataset_id, as_dataframe=as_dataframe)

    def get_form_columns(self, dataset_id: str, as_dataframe: bool = False):
        return self.endpoints.get_form_columns(
            dataset_id=dataset_id, as_dataframe=as_dataframe
        )

    def update_dataset(
        self, dataset_id: str, payload: Union[pl.DataFrame, dict, list, str], **kwargs
    ):
        return self.endpoints.update_dataset(dataset_id, payload, **kwargs)

    def upload_csv_file(self, dataset_id: str, filepath: str, **kwargs):
        return self.endpoints.upload_csv_file(dataset_id, filepath, **kwargs)

    def upload_csv_fileobj(
        self, dataset_id: str, fileobj: BinaryIO, filename: str, **kwargs
    ):
        return self.endpoints.upload_csv_fileobj(
            dataset_id, fileobj, filename, **kwargs
        )

    def upload_csv(self, dataset_id: str, source, filename: str | None = None):
        if isinstance(source, (str, Path)):
            return self.upload_csv_file(dataset_id=dataset_id, filepath=source)
        if hasattr(source, "read"):
            if filename is None:
                filename = getattr(source, "name", "upload.csv")
            return self.upload_csv_fileobj(
                dataset_id, fileobj=source, filename=filename
            )
        raise TypeError("source must be a path or a binary file-like object")

    def get_job_status(self, submission_id: str, **kwargs) -> Optional[str]:
        return self.endpoints.get_job_status(submission_id, **kwargs)

    # ---------- Public methods (wrapping resources) ----------
    def decode_df_choices(
        self,
        df: pl.DataFrame,
        dsid: str,
        *,
        mode: str = "replace",
        label_suffix: str = "_LABEL",
    ) -> pl.DataFrame:
        return self.endpoints.decode_df_choices(
            df=df, dsid=dsid, mode=mode, label_suffix=label_suffix
        )

    # ---------- Context management ----------
    def close(self):
        self.api.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
