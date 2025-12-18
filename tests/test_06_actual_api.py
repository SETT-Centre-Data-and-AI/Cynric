import os
from io import BytesIO
from pathlib import Path

import pandas as pd
import pytest
from dotenv import load_dotenv

from cynric.api.queue import BCPlatformsQueue

load_dotenv()
TOKEN = os.getenv("BC_TOKEN")
BASE_URL = os.getenv("DEFAULT_BASE_URL")
TEST_DATASET_ID = "ds100691"
TEST_DATA_FILE = Path(__file__).parent / "data" / "Fake_Clinical_Data.csv"


pytestmark = pytest.mark.internal


def connect():
    bcp = BCPlatformsQueue(token=TOKEN, base_url=BASE_URL)
    if not bcp.check_connection():
        raise Exception("Issue with BCP connection")

    return bcp


def delete_test_data(dataset_id=TEST_DATASET_ID):
    bcp = connect()
    resp = bcp.get_dataset(dataset_id=dataset_id)

    to_del = resp.content.decode()

    delete_headers = {
        "Accept": "*/*",
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
    }

    del_endpoint = f"/datasets/{dataset_id}/rows"
    del_resp = bcp.api.request(
        method="DELETE",
        path_or_url=del_endpoint,
        headers=delete_headers,
        data_body=to_del,
    )

    print(del_resp)


def test_delete():
    delete_test_data()


def test_upload_csv_and_wait(dataset_id=TEST_DATASET_ID):

    bcp = connect()
    response = bcp.upload_csv_and_wait(
        dataset_id=dataset_id,
        source=TEST_DATA_FILE,
        poll_rate=5,
    )

    assert response == "COMPLETED"


def test_upload_fileobj_and_wait(dataset_id=TEST_DATASET_ID):
    bcp = connect()

    df = pd.read_csv(TEST_DATA_FILE)

    def create_csv_in_memory(df: pd.DataFrame) -> BytesIO:
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        buffer = BytesIO(csv_bytes)
        buffer.seek(0)
        return buffer

    csv_mem = create_csv_in_memory(df)

    response = bcp.upload_csv_and_wait(
        dataset_id=dataset_id,
        source=csv_mem,
        filename="test_csv_in_memory",
        poll_rate=5,
    )

    assert response == "COMPLETED"
