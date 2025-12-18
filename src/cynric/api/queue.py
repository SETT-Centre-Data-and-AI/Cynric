import json
import time
from io import BytesIO
from logging import Logger
from pathlib import Path

import requests

from cynric.api.bc import BCPlatforms
from cynric.api.logger import get_logger

log = get_logger(__name__)


class BCPlatformsQueue(BCPlatforms):
    """Extension of BCPlatforms to include queue-related methods."""

    logger: Logger = log

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = kwargs.get("logger", log)

    def _extract_submission_id(self, response: requests.Response) -> str:
        """Pull the submission/job identifier out of an upload response."""
        submission_id = json.loads(response.content.decode())[
            "submissionID: "
        ]  # intentional colon and space

        return submission_id

    # Just deals with file uploading and job status polling. File chunking managed elsewhere.
    def _upload_csv_and_wait(
        self,
        dataset_id: str,
        source: str | Path | BytesIO,
        filename: str | None = None,
        poll_rate: int = 5,
    ):
        """Upload a file to a dataset, using the queue system to monitor job status."""

        response = self.upload_csv(
            dataset_id=dataset_id, source=source, filename=filename
        )

        submission_id = self._extract_submission_id(response)

        while True:
            status = self.endpoints.get_job_status(submission_id)
            if status in ["COMPLETED", "FAILED"]:
                self.logger.debug(f"{dataset_id}: {status}")
                break
            self.logger.debug(f"{dataset_id}: {status}. Waiting {poll_rate} seconds...")
            time.sleep(poll_rate)

        return status

    def upload_csv_and_wait(
        self,
        dataset_id: str,
        source: str | Path | BytesIO,
        filename: str | None = None,
        poll_rate: int = 5,
    ):
        return self._upload_csv_and_wait(
            dataset_id=dataset_id, source=source, filename=filename, poll_rate=poll_rate
        )
