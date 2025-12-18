import random

from valediction.datasets.datasets import Dataset  # type: ignore

from cynric.demo import DEMO_DATA, DEMO_DICTIONARY  # type: ignore

# Global Testing Support Functions
GOOD_URL = "https://example.com"
GOOD_TOKEN = (
    "eyJhbGciOiAiSFMyNTYifQ.eyJzdWIiOiAidXNlciIsICJleHAiOiA0MTAyNDQ0ODAwfQ.c2lnbmF0dXJl"
)

BAD_URL = "example.com"
BAD_TOKEN = "!!!.eyJzdWIiOiAidXNlciIsICJleHAiOiA0MTAyNDQ0ODAwfQ.c2lnbmF0dXJl"
EXPIRED_TOKEN = "eyJhbGciOiAiSFMyNTYifQ.eyJzdWIiOiAidXNlciIsICJleHAiOiAxfQ.c2lnbmF0dXJl"


# Helpers
def random_table_name(length: int = 5) -> str:
    return "d" + "".join(str(random.randint(0, 9)) for _ in range(length))


def get_dataset() -> Dataset:
    dataset = Dataset().create_from(DEMO_DATA)
    dataset.import_dictionary(DEMO_DICTIONARY)
    return dataset


def get_valid_table_map() -> dict[str, str]:
    dataset = get_dataset()
    table_map = dict()
    for table in dataset:
        table_map[table.name] = random_table_name()
    return table_map


def get_actual_table_map() -> dict[str, str]:
    return get_valid_table_map()  # TODO: refactor to point to actual demo tables


def get_incorrect_table_map() -> dict[str, str]:
    dataset = get_dataset()
    table_map = dict()
    for table in dataset:
        table_map[table.name] = random_table_name()
    table_map["an_additional_table"] = random_table_name()
    return table_map
