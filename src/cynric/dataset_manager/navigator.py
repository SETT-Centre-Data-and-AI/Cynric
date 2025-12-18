from __future__ import annotations

import builtins
import ast
from datetime import datetime, timedelta
import json
from pathlib import Path
import re
from typing import (
    Any,
    Dict,
    Iterable,
    List,
)

from cynric.api.bc import BCPlatforms
from cynric.credentials.resolution import resolve_credentials


# -------------------------------
# Navigator utilities
# -------------------------------
class Navigator:

    def __init__(
        self,
        token: str = "",
        base_url: str = "",
    ):
        self.token: str = token
        self.base_url: str = base_url
        self.datasets: str | None = None
        self.dataset_refreshed: datetime | None = None
        self.cache_time: float | timedelta = 300.0

        self.__check_credentials()

    # Checks
    def __check_credentials(self) -> None:
        """Checks credentials are valid if provided, or fetches from OS credential
        storage."""
        self.base_url, self.token = resolve_credentials(
            token=self.token, base_url=self.base_url
        )

        self.api: BCPlatforms = BCPlatforms(token=self.token, base_url=self.base_url)

    def get_datasets(self, force: bool = False):
        """Get (and cache) the datasets list.

        Re-fetches datasets when:
        - ``force`` is True
        - datasets have never been fetched (``dataset_refreshed`` is None)
        - cached datasets are older than ``cache_time``

        Args:
            force: Always refresh from the API, ignoring any cached datasets.
            cache_time: Cache duration in seconds (or a ``timedelta``). Use 0 to
                disable caching (always refresh).

        Returns:
            The cached dataset payload returned by the API.
        """
        cache_seconds = (
            self.cache_time.total_seconds()
            if isinstance(self.cache_time, timedelta)
            else float(self.cache_time)
        )

        now = datetime.now()
        should_refresh = (
            force or self.datasets is None or self.dataset_refreshed is None
        )

        if not should_refresh:
            if cache_seconds <= 0:
                should_refresh = True
            else:
                age_seconds = (now - self.dataset_refreshed).total_seconds()
                should_refresh = age_seconds > cache_seconds

        if should_refresh:
            response = self.api.get_datasets_list()
            self.datasets = response.json()
            self.dataset_refreshed = datetime.now()

        return self.datasets

    # def print_dataset_folders(
    #     self,
    #     root_dir: str | Path = "root",
    #     max_depth: int | None = None,
    #     **kwargs,
    # ) -> str:

    #     datasets_list = self.get_datasets()

    #     _created_paths = self._create_dataset_folders(datasets_list, root_dir, **kwargs)

    #     return self._print_dataset_folders(_created_paths, max_depth=max_depth)
    def search_dataset_folders(
        self,
        search: str = "",
        *,
        print: bool = True,
        root_dir: str | Path = "root",
        include_datasets: bool = False,
        case_sensitive: bool = False,
        **kwargs,
    ) -> list[Path]:
        """Search dataset folders (and optionally dataset leaf files).

        - Default behaviour: substring search by name. Dataset leaves (the
          ``<name> (<id>)`` files) are only returned when ``include_datasets`` is True.
        - Path search: when ``search`` contains ``/`` or ``\\``, treat it as a relative
          path (ignoring ``root_dir``). Matches return the *entire subtree* beneath the
          matched path (directories and files).

        Returns a sorted list of matching Paths. Uses the same payload as
        ``_create_dataset_folders`` to ensure paths exist before searching.
        """

        datasets_list = self.get_datasets()

        created_paths = self._create_dataset_folders(datasets_list, root_dir, **kwargs)

        root_path = Path(root_dir)

        raw_search = search.strip()
        term = raw_search if case_sensitive else raw_search.lower()
        is_path_query = ("/" in raw_search) or ("\\" in raw_search)

        def _matches(name: str) -> bool:
            candidate = name if case_sensitive else name.lower()
            return term in candidate

        def _relative_posix(path: Path) -> str:
            try:
                rel = path.relative_to(root_path)
            except ValueError:
                rel = path
            rel_str = rel.as_posix()
            return "" if rel_str == "." else rel_str.lstrip("/")

        # Normalise the path query (drop the root prefix and normalise separators)
        path_term = raw_search.replace("\\", "/").strip("/")
        if is_path_query and root_path.name:
            root_name = root_path.name.replace("\\", "/").strip("/")
            if path_term == root_name:
                path_term = ""
            elif path_term.startswith(f"{root_name}/"):
                path_term = path_term[len(root_name) + 1 :]
        path_term_norm = path_term if case_sensitive else path_term.lower()

        def _path_is_within_query(path: Path) -> bool:
            if not is_path_query:
                return False
            candidate = _relative_posix(path)
            candidate_norm = candidate if case_sensitive else candidate.lower()
            if not path_term_norm:
                return True  # empty path term matches everything under root
            return candidate_norm == path_term_norm or candidate_norm.startswith(
                f"{path_term_norm}/"
            )

        dirs: set[Path] = {root_path}
        files: set[Path] = set()

        for dataset_path in created_paths:
            files.add(dataset_path)

            for parent in dataset_path.parents:
                if parent == root_path.parent:
                    break
                dirs.add(parent)
                if parent == root_path:
                    break

            if dataset_path.is_dir():
                for path in dataset_path.rglob("*"):
                    if path.is_dir():
                        dirs.add(path)
                    else:
                        files.add(path)

        if is_path_query:
            # Subtree search: include all dirs/files within the matched relative path.
            results: set[Path] = {p for p in dirs if _path_is_within_query(p)}
            results.update({p for p in files if _path_is_within_query(p)})
        else:
            results = {p for p in dirs if _matches(str(p))}

        # If a dataset leaf file matches but files are excluded, include its parents so
        # the containing subdirectories still appear in results.
        if not include_datasets and not is_path_query:
            for dataset_path in created_paths:
                if _matches(dataset_path.name):
                    for parent in dataset_path.parents:
                        if parent == root_path.parent:
                            break
                        results.add(parent)
                        if parent == root_path:
                            break

        if include_datasets and not is_path_query:
            for file_path in files:
                if _matches(file_path.name):
                    results.add(file_path)

        sorted_search = sorted(results, key=lambda p: p.as_posix())

        if print:
            builtins.print(self._print_dataset_folders(paths=sorted_search))

        else:
            return sorted_search

    def _coerce_records(self, payload: Any) -> List[Dict[str, Any]]:
        """Normalize a JSON-like payload (path, string, dict, or list) to records."""
        if isinstance(payload, bytes):
            payload = payload.decode()

        if isinstance(payload, (list, dict)):
            parsed = payload
        elif isinstance(payload, (str, Path)):
            path = Path(payload)
            raw_content = (
                path.read_text(encoding="utf-8") if path.exists() else str(payload)
            )
            try:
                parsed = json.loads(raw_content)
            except json.JSONDecodeError:
                try:
                    parsed = ast.literal_eval(raw_content)
                except Exception:
                    parsed = ast.literal_eval(f"[{raw_content}]")
        else:
            raise TypeError(f"Unsupported payload type: {type(payload)}")

        if isinstance(parsed, dict):
            return [parsed]
        if isinstance(parsed, list):
            return [x for x in parsed if isinstance(x, dict)]
        raise TypeError(f"Expected dict or list of dicts, got {type(parsed)}")

    def _slugify(self, value: str) -> str:
        """Make a filesystem-friendly slug."""
        value = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("_")
        return value or "dataset"

    def _strip_owner_prefix(self, value: str) -> str:
        """Drop a leading '<owner> ' prefix if present."""
        value = value.strip()
        if value.startswith("<") and ">" in value:
            return value.split(">", 1)[1].strip()
        return value

    def _create_dataset_folders(
        self,
        data: str | Path | List[Dict[str, Any]] | Dict[str, Any],
        root_dir: str | Path,
        *,
        name_key: str = "name",
        folder_key: str = "folder",
        id_key: str = "id",
        write_metadata: bool = False,
        metadata_filename: str = "metadata.json",
        cleanup_metadata: bool = True,
        create: bool = False,
    ) -> list[Path]:
        """Create a navigable folder structure from a JSON dataset descriptor.

        - Folders are nested according to the `folder` value
        - Each dataset gets a *file* named `<slugified-name> (<id>)` (the dataset leaf is
          treated like a file so it can be excluded when searching without files)
        - Optional metadata for each dataset can be written alongside (or cleaned up)
        - Optionally writes an INDEX.md with a tree view at the root
        - If ``create`` is False, this returns the would-be paths without touching disk
        """
        root = Path(root_dir)

        records = self._coerce_records(data)
        created_paths: list[Path] = []

        for record in records:
            folder_parts = [
                part for part in str(record.get(folder_key, "")).split("/") if part
            ]
            raw_name = str(record.get(name_key, record.get(id_key, "dataset")))
            dataset_name = self._strip_owner_prefix(raw_name)
            dataset_id = str(record.get(id_key, "unknown"))
            dataset_dirname = f"{self._slugify(dataset_name)} ({dataset_id})"

            dataset_parent = root.joinpath(*folder_parts)
            if create:
                dataset_parent.mkdir(parents=True, exist_ok=True)
            dataset_path = dataset_parent / dataset_dirname

            # If the name already exists as a directory, fall back to a marker file to
            # avoid destructive changes.
            if dataset_path.exists() and dataset_path.is_dir():
                dataset_path = dataset_parent / f"{dataset_dirname}.dataset"

            if create and not dataset_path.exists():
                dataset_path.touch()

            if create and write_metadata:
                metadata_path = dataset_path.with_suffix(f".{metadata_filename}")
                metadata_path.write_text(
                    json.dumps(record, indent=2, ensure_ascii=False), encoding="utf-8"
                )
            elif create and cleanup_metadata:
                metadata_path = dataset_path.with_suffix(f".{metadata_filename}")
                if metadata_path.exists():
                    metadata_path.unlink()
            created_paths.append(dataset_path)

        return created_paths

    def _print_dataset_folders(
        self,
        paths: Iterable[Path | str],
        *,
        nested: bool = True,
        root_name: str | None = None,
        max_depth: int | None = None,
    ) -> str:
        """Return an ASCII tree view for a collection of paths.

        If ``nested`` is False, paths are joined with newlines in their string form.
        If ``max_depth`` is provided, limit traversal to that many levels beneath the
        common root (0 keeps only the root line).
        """

        path_objs = [Path(p) for p in paths]
        if not path_objs:
            return ""

        if not nested:
            return "\n".join(str(p) for p in path_objs)

        parts_list = [list(p.parts) for p in path_objs]

        def _common_prefix(lists: list[list[str]]) -> list[str]:
            prefix: list[str] = []
            for chunk in zip(*lists):
                if all(part == chunk[0] for part in chunk):
                    prefix.append(chunk[0])
                else:
                    break
            return prefix

        common_prefix = _common_prefix(parts_list)
        display_root = root_name or ("/".join(common_prefix) if common_prefix else ".")

        def _without_prefix(parts: list[str], prefix: list[str]) -> list[str]:
            return (
                parts[len(prefix) :]
                if prefix and parts[: len(prefix)] == prefix
                else parts
            )

        tree: dict[str, dict] = {}
        for parts in parts_list:
            trimmed_parts = _without_prefix(parts, common_prefix)
            cursor = tree
            for part in trimmed_parts:
                cursor = cursor.setdefault(part, {})

        lines = [display_root]

        depth_limit = max_depth if max_depth is None or max_depth >= 0 else None

        def _walk(node: dict[str, dict], prefix: str, level: int) -> None:
            if depth_limit is not None and level > depth_limit:
                return
            items = sorted(node.items(), key=lambda kv: kv[0])
            for idx, (name, child) in enumerate(items):
                is_last = idx == len(items) - 1
                connector = "`-- " if is_last else "|-- "
                lines.append(f"{prefix}{connector}{name}")
                extension = "    " if is_last else "|   "
                _walk(child, prefix + extension, level + 1)

        _walk(tree, "", 1)
        return "\n".join(lines)
