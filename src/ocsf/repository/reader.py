"""Read schema definition files from a directory into a Repository."""

import json
import dacite

from pathlib import Path
from .repository import Repository, DefinitionFile
from .definitions import AnyDefinition
from .helpers import REPO_PATHS, RepoPaths, Pathlike, sanitize_path, path_defn_t

from ocsf.schema import keys_to_names


def _to_defn(path: Pathlike, raw_data: str, preserve_raw_data: bool) -> DefinitionFile[AnyDefinition]:
    """Convert a path and raw JSON string into a DefinitionFile."""
    kind = path_defn_t(path)

    path = sanitize_path(path)
    defn = DefinitionFile[kind](path)

    if preserve_raw_data:
        defn.raw_data = raw_data

    data = json.loads(raw_data)
    defn.data = dacite.from_dict(kind, keys_to_names(data))

    return defn


def _walk_path(path: Path, repo: Repository, preserve_raw_data: bool) -> None:
    """Recursively walk a directory, reading schema definition files into a Repository."""
    for entry in path.iterdir():
        if entry.is_file() and entry.suffix == ".json":
            with open(entry) as file:
                defn = _to_defn(entry, file.read(), preserve_raw_data)
                repo[sanitize_path(entry)] = defn

        elif entry.is_dir() and (
            entry.name in REPO_PATHS or entry.parent.name in REPO_PATHS or RepoPaths.EVENTS.value in entry.parts
        ):
            _walk_path(entry, repo, preserve_raw_data)


def read_repo(path: Pathlike, preserve_raw_data: bool = False) -> Repository:
    """Load a directory of schema definition files into a Repository."""
    repo = Repository()

    if not isinstance(path, Path):
        path = Path(path)
    _walk_path(path, repo, preserve_raw_data)

    return repo
