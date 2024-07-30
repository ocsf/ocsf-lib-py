"""Helper functions and enums for working with repositories."""

from enum import StrEnum
from pathlib import PurePath

from .definitions import (
    ObjectDefn,
    EventDefn,
    IncludeDefn,
    ProfileDefn,
    DictionaryDefn,
    CategoriesDefn,
    VersionDefn,
    ExtensionDefn,
    AnyDefinition,
)

Pathlike = PurePath | str
RepoPath = str


class RepoPaths(StrEnum):
    """Top level paths in a repository."""

    OBJECTS = "objects"
    EVENTS = "events"
    EXTENSIONS = "extensions"
    INCLUDES = "includes"
    PROFILES = "profiles"


REPO_PATHS = tuple([e.value for e in RepoPaths])


class SpecialFiles(StrEnum):
    """Files in a repository."""

    DICTIONARY = "dictionary.json"
    CATEGORIES = "categories.json"
    VERSION = "version.json"
    EXTENSION = "extension.json"

    @staticmethod
    def contains(path: str) -> bool:
        return path in [e.value for e in SpecialFiles]


SPECIAL_FILES = tuple([e.value for e in SpecialFiles])


def sanitize_path(*path: Pathlike) -> RepoPath:
    """Ensure a path is a valid repository path."""
    p = PurePath(*path)

    idx = 0
    loc = -1

    while idx < len(p.parts) and loc < 0:
        part = p.parts[idx]
        if part in REPO_PATHS or part in SPECIAL_FILES:
            loc = idx
        else:
            idx += 1

    if loc < 0:
        raise ValueError(f"Invalid key: {p} isn't an allowed file or directory.")

    parts = p.parts[idx:]

    if parts[0] == RepoPaths.EXTENSIONS.value:
        if len(parts) < 3:
            raise ValueError(f"Invalid key: {p} is missing extension name or contents.")

        if len(parts) > 3 and parts[2] not in REPO_PATHS:
            raise ValueError(f"Invalid key: {parts[2]} isn't an allowed directory.")

        if len(parts) == 3 and parts[2] not in SPECIAL_FILES:
            raise ValueError(f"Invalid key: {parts[2]} isn't an allowed filename.")

    return PurePath(*parts).as_posix()


def as_path(*args: Pathlike) -> RepoPath:
    """Convert path parts as Paths and strings to a single string."""
    return PurePath(*args).as_posix()


def short_name(*args: Pathlike) -> str:
    """The file name of a repository path."""
    return PurePath(*args).stem


def extension(*args: Pathlike) -> str | None:
    """The extension of a repository path, or None if the path is not in an
    extension directory.
    """
    p = as_path(*args)
    if p.startswith(RepoPaths.EXTENSIONS):
        return PurePath(*args).parts[1]
    return None


def extensionless(*args: Pathlike) -> RepoPath:
    """The repository path without an extension prefix."""
    p = as_path(*args)
    if p.startswith(RepoPaths.EXTENSIONS):
        return as_path(*PurePath(p).parts[2:])
    else:
        return p


def category(*args: Pathlike) -> str | None:
    """The category of a repository path to an event."""
    k = PurePath(extensionless(*args))
    if k.parts[0] == RepoPaths.EVENTS and len(k.parts) > 2:
        return as_path(*k.parts[1:-1])

    return None


def categoryless(*args: Pathlike) -> str:
    """Return a repository path without an event category prefix."""
    k = PurePath(*args)
    if extension(*args) is not None:
        idx = 2
        min = 4
    else:
        idx = 0
        min = 2

    if k.parts[idx] == RepoPaths.EVENTS and len(k.parts) > min:
        return as_path(*k.parts[0 : 1 + idx] + (k.parts[-1],))

    return as_path(*args)


def path_defn_t(*path_parts: Pathlike) -> type[AnyDefinition]:
    """Return the expected definition type for a repository path."""
    path = sanitize_path(*path_parts)
    parts = PurePath(path).parts

    match parts:
        case (RepoPaths.OBJECTS.value, *_, _):
            return ObjectDefn
        case (RepoPaths.EVENTS.value, *_, _):
            return EventDefn
        case (RepoPaths.INCLUDES.value, *_, _):
            return IncludeDefn
        case (RepoPaths.PROFILES.value, *_, _):
            return ProfileDefn
        case (RepoPaths.EXTENSIONS.value, *_, _):
            return path_defn_t(*parts[2:])
        case _:
            ...

    match parts[-1]:
        case SpecialFiles.DICTIONARY.value:
            return DictionaryDefn
        case SpecialFiles.CATEGORIES.value:
            return CategoriesDefn
        case SpecialFiles.VERSION.value:
            return VersionDefn
        case SpecialFiles.EXTENSION.value:
            return ExtensionDefn
        case _:
            ...

    raise ValueError(f"{path} isn't a recognized repository path.")
