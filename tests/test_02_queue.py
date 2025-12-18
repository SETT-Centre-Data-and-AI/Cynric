from unittest.mock import MagicMock

import pytest

from cynric.api.queue import BCPlatformsQueue


def test_upload_file_and_wait_polls_until_completion(monkeypatch, tmp_path):
    dummy_csv = tmp_path / "dummy.csv"
    dummy_csv.write_text("col1,col2\n1,2\n", encoding="utf-8")

    queue = object.__new__(BCPlatformsQueue)

    endpoints = MagicMock()
    upload_response = MagicMock()
    endpoints.upload_csv_file.return_value = upload_response
    endpoints.get_job_status.side_effect = ["QUEUED", "PROCESSING", "COMPLETED"]
    queue.endpoints = endpoints

    queue._extract_submission_id = MagicMock(return_value="submission-123")

    monkeypatch.setattr("cynric.api.queue.time.sleep", lambda _: None)

    status = queue.upload_csv_and_wait(
        dataset_id="dataset-abc",
        source=str(dummy_csv),
        poll_rate=0,
    )

    queue._extract_submission_id.assert_called_once_with(upload_response)
    endpoints.upload_csv_file.assert_called_once_with("dataset-abc", str(dummy_csv))
    assert endpoints.get_job_status.call_count == 3
    assert all(
        call.args[0] == "submission-123"
        for call in endpoints.get_job_status.call_args_list
    )
    assert status == "COMPLETED"


if __name__ == "__main__":
    pytest.main([__file__])
