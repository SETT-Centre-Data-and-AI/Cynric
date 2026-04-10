import os
from pathlib import Path

import pytest
from support import (
    DEMO_DATA,
    DEMO_DICTIONARY,
)
from valediction.datasets.datasets import Dataset  # type: ignore

from cynric.uploading.convenience import validate_and_upload
from cynric.uploading.uploading import Uploader

RUNNING_IN_GITHUB_ACTIONS = os.getenv("GITHUB_ACTIONS", "").lower() == "true"

pytestmark = [
    pytest.mark.internal,
    pytest.mark.skipif(
        RUNNING_IN_GITHUB_ACTIONS,
        reason="Real upload tests only run locally.",
    ),
]

# ----- OVERRIDES -------#
# TODO - Replace with DEMO_DATA when uploaded to SDE
GOOD_TOKEN = os.getenv("BC_TOKEN")
GOOD_URL = os.getenv("DEFAULT_BASE_URL")
DEMO_DATA_FILENAME = "Fake_Clinical_Data"


def get_actual_table_map():
    DEMO_DATA_MAP = {DEMO_DATA_FILENAME: "ds100691"}
    return DEMO_DATA_MAP


def get_dataset() -> Dataset:

    data_path = Path(__file__).parent / "data" / f"{DEMO_DATA_FILENAME}.csv"
    dataset = Dataset().create_from(data_path)
    dataset.generate_dictionary(primary_keys={DEMO_DATA_FILENAME: ["PATIENT_ID"]})

    return dataset


# -----------------------#


def test_uploading_validated_dataset() -> None:
    dataset = get_dataset()
    dataset.validate()
    table_map = get_actual_table_map()
    uploader = Uploader(
        dataset=dataset, target_table_map=table_map, token=GOOD_TOKEN, base_url=GOOD_URL
    )
    # raise NotImplementedError  # TODO: @georgm8 move to local test only, or use a safe website to expect a particular error against?
    uploader.upload(feedback=False)


def test_validate_and_upload() -> None:
    dataset = get_dataset()
    dataset.validate()
    table_map = get_actual_table_map()
    uploader = Uploader(
        dataset=dataset,
        target_table_map=table_map,
        token=GOOD_TOKEN,
        base_url=GOOD_URL,
    )
    # raise NotImplementedError  # TODO: @georgm8 move to local test only, or use a safe website to expect a particular error against?
    uploader.validate_and_upload(feedback=False)


# Test Convenience Function
def test_validate_and_upload_conv() -> None:
    dataset = get_dataset()
    dataset.validate()
    table_map = get_actual_table_map()
    # raise NotImplementedError  # TODO: @georgm8 move to local test only, or use a safe website to expect a particular error against?
    validate_and_upload(
        dataset,
        table_map,
        feedback=False,
        token=GOOD_TOKEN,
        base_url=GOOD_URL,
    )


def test_validate_and_upload_pointed() -> None:
    # raise NotImplementedError  # TODO: @georgm8 move to local test only, or use a safe website to expect a particular error against?
    validate_and_upload(
        dataset=DEMO_DATA,
        target_table_map=get_actual_table_map(),
        feedback=False,
        dictionary=DEMO_DICTIONARY,
        token=GOOD_TOKEN,
        base_url=GOOD_URL,
    )
