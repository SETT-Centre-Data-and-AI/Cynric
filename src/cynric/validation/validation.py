from __future__ import annotations

from pathlib import Path

from pandas import DataFrame  # type: ignore
from valediction.datasets.datasets import Dataset  # type: ignore
from valediction.dictionary.model import Dictionary  # type: ignore
from valediction.exceptions import DataDictionaryError  # type: ignore


def validate(
    dataset: str | Path | dict[str, DataFrame] | Dataset,
    dictionary: Dictionary | str | Path | None = None,
    *,
    import_data: bool = False,
    chunk_size: int | None = 10_000_000,
    feedback: bool = True,
) -> Dataset:
    _dataset = (
        dataset if isinstance(dataset, Dataset) else Dataset().create_from(dataset)
    )

    if dictionary is not None:
        _dataset.import_dictionary(dictionary)
    else:
        if _dataset.dictionary is None:
            raise DataDictionaryError(
                "A dictionary argument must be provided when passing in a path to a dataset "
                "or a dict of DataFrames. If a pre-prepared Dataset is passed without a "
                "Dictionary already attached, this must also be provided."
            )

    if import_data:
        _dataset.import_data()
    _dataset.validate(chunk_size=chunk_size, feedback=feedback)

    return _dataset
