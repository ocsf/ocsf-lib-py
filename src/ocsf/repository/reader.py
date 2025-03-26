"""Read schema definition files from a directory into a Repository."""

import json
from pathlib import Path
from typing import Callable

import dacite

from ocsf.schema import keys_to_names

from .definitions import AnyDefinition
from .helpers import REPO_PATHS, Pathlike, RepoPaths, path_defn_t, sanitize_path
from .repository import DefinitionFile, Repository


def _to_defn(path: Pathlike, raw_data: str, preserve_raw_data: bool) -> DefinitionFile[AnyDefinition]:
    """Convert a path and raw JSON string into a DefinitionFile."""
    kind = path_defn_t(path)

    path = sanitize_path(path)
    defn = DefinitionFile[kind](path)

    if preserve_raw_data:
        defn.raw_data = raw_data

    data = json.loads(raw_data)
    try:
        defn.data = dacite.from_dict(kind, keys_to_names(data))
    except dacite.DaciteError as de:
        raise Exception(f"Failed to parse {path}") from de

    return defn


RenameFn = Callable[[Path], Path]


def _walk_path(path: Path, repo: Repository, preserve_raw_data: bool, rename_fn: RenameFn | None = None) -> None:
    """Recursively walk a directory, reading schema definition files into a Repository."""

    assert path.is_dir(), "Path must be a directory."

    for entry in path.iterdir():
        if entry.is_file() and entry.suffix == ".json":
            with open(entry) as file:
                if rename_fn is not None:
                    dest = rename_fn(entry)
                else:
                    dest = entry
                defn = _to_defn(dest, file.read(), preserve_raw_data)
                repo[sanitize_path(dest)] = defn

        elif entry.is_dir() and (
            entry.name in REPO_PATHS or entry.parent.name in REPO_PATHS or RepoPaths.EVENTS.value in entry.parts
        ):
            _walk_path(entry, repo, preserve_raw_data, rename_fn)


def read_repo(path: Pathlike, preserve_raw_data: bool = False) -> Repository:
    """Load a directory of schema definition files into a Repository."""
    repo = Repository()

    if not isinstance(path, Path):
        path = Path(path)
    _walk_path(path, repo, preserve_raw_data)

    return repo


def add_extensions(extn_path: Pathlike, repo: Repository, preserve_raw_data: bool = False) -> None:
    """Add a custom extensions directory to a Repository."""
    if not isinstance(extn_path, Path):
        extn_path = Path(extn_path)

    def _rename_extensions(path: Path) -> Path:
        return RepoPaths.EXTENSIONS.value / path.relative_to(extn_path)

    _walk_path(extn_path, repo, preserve_raw_data, rename_fn=_rename_extensions)


def add_extension(extn_path: Pathlike, repo: Repository, preserve_raw_data: bool = False) -> None:
    """Add a custom extension to a Repository by its path."""
    if not isinstance(extn_path, Path):
        extn_path = Path(extn_path)

    extn_base = Path(RepoPaths.EXTENSIONS.value, extn_path.name)

    def _rename_extension(path: Path) -> Path:
        return extn_base / path.relative_to(extn_path)

    _walk_path(extn_path, repo, preserve_raw_data, rename_fn=_rename_extension)
