import re
from pathlib import Path
from pprint import pprint
from typing import Iterable, List, Tuple
from rapidfuzz import fuzz

from cynric.api.bc import BCPlatforms


def _list_filenames(root: str | Path, recursive: bool = True) -> List[Path]:
    """Return list of file Paths relative to root."""
    root_path = Path(root).expanduser()
    if recursive:
        return [p for p in root_path.rglob("*") if p.is_file()]
    return [p for p in root_path.glob("*") if p.is_file()]


def _strip_substrings(text: str, substrings: Iterable[str]) -> str:
    """Remove each substring (case-insensitive) from text."""
    result = text
    for sub in substrings:
        if not sub:
            continue
        pattern = re.compile(re.escape(sub), flags=re.IGNORECASE)
        result = pattern.sub("", result)
    return result.strip()


def _find_matches(
    query: str, filenames: Iterable[Path], min_score: float = 70.0
) -> List[Tuple[Path, float]]:
    """
    Match `query` against the stem of each Path in `filenames`.

    Returns a list of (Path, score) sorted by descending score.
    Score is in the range 0-100 (higher is better). Only results at or above
    `min_score` are included. Performs simple substring matching first; if none
    found, falls back to fuzzy matching.
    """
    results: List[Tuple[Path, float]] = []
    q = query.lower()

    # Prefer exact substring-style matches first
    for path in filenames:
        stem = path.stem
        lower_stem = stem.lower()
        if q in lower_stem or lower_stem in q:
            results.append((path.resolve(), 100.0))

    if results:
        results.sort(key=lambda x: x[1], reverse=True)
        return results

    # Fuzzy fallback
    for path in filenames:
        stem = path.stem
        score = fuzz.QRatio(query, stem)
        if score >= min_score:
            results.append((path.resolve(), score))

    results.sort(key=lambda x: x[1], reverse=True)
    return results


def map_files_to_datasets(
    directory,
    dataset_list,
    min_score: float,
    remove_substrings: Iterable[str] | None = None,
    recursive=False,
):
    filenames = _list_filenames(directory, recursive=recursive)

    filename_ds_mapping = {}
    ambiguous_matches: dict[str, List[Tuple[Path, float]]] = {}
    substrings = remove_substrings or ()

    for d in dataset_list:
        author, dataset_name = d["name"].split(" ")
        cleaned_dataset_name = _strip_substrings(dataset_name, substrings)
        # Avoid empty query if everything was stripped
        query = cleaned_dataset_name if cleaned_dataset_name else dataset_name
        matches = _find_matches(query=query, filenames=filenames, min_score=min_score)

        if len(matches) == 0:
            raise Exception(f"No matches were found for {dataset_name}. Please review")

        if len(matches) > 1:
            ambiguous_matches[f"{dataset_name} {d['id']}"] = matches
            continue

        filename_ds_mapping[matches[0][0]] = d["id"]

    if ambiguous_matches:
        print("Ambiguous matches detected. Edit the mapping below to resolve them.")
        print("Resolved filename -> dataset_id:")
        pprint(filename_ds_mapping)
        print("\nAmbiguous dataset_name -> [(path, score) ...]:")
        pprint(ambiguous_matches)

    return filename_ds_mapping