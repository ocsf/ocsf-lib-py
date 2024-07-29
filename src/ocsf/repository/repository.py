"""A representation of an OCSF repository.

A `Repository` is a collection of paths (`objects/base.json`, `dictionary.json`,
etc.) and the definition files at those paths.

The `DefinitionFile` class represents a single file in the repository. It
contains a `Definition` – a data class representing the type of definition for
that path – and, optionally, the raw data from the file as a `str`.

"""

from dataclasses import dataclass
from pathlib import PurePath
from typing import Optional, Iterable, TypeVar, Generic, cast

from .helpers import RepoPath, RepoPaths, path_defn_t
from .definitions import AnyDefinition, ProfileDefn, DefinitionData


DefnT = TypeVar("DefnT", bound=DefinitionData)


@dataclass
class DefinitionFile(Generic[DefnT]):
    """A file in the repository."""

    path: RepoPath
    """The path to the file in the repository. This should always correspond to
    the key in the repository's contents.
    """

    raw_data: Optional[str] = None
    """The raw data from the file, as a string. This can be useful for debugging but is not required."""

    data: Optional[DefnT] = None
    """The parsed data from the file as a DefinitionData dataclass. This should
    be an instance of the expected definition type for the path.
    """

    def short_name(self) -> str:
        """Return the filename of the file without the path or extension."""
        return PurePath(self.path).stem


class Repository:
    """An OCSF schema repository."""

    def __init__(self, contents: Optional[dict[RepoPath, DefinitionFile[AnyDefinition]]] = None):
        if contents is not None:
            self._contents = contents
        else:
            self._contents: dict[RepoPath, DefinitionFile[AnyDefinition]] = {}

    def __getitem__(self, path: RepoPath) -> DefinitionFile[AnyDefinition]:
        """Return the definition file at the given path."""
        return self._contents[path]

    def __delitem__(self, path: RepoPath) -> None:
        """Remove the definition file at the given path."""
        del self._contents[path]

    def __contains__(self, path: RepoPath) -> bool:
        """Return whether the repository contains a definition file at the given path."""
        return path in self._contents

    def __len__(self) -> int:
        """Return the number of definition files in the repository."""
        return len(self._contents)

    def __setitem__(self, path: RepoPath, file: DefinitionFile[AnyDefinition]) -> None:
        """Add a definition file to the repository."""
        file.path = path
        self._contents[path] = file

    def files(self) -> Iterable[DefinitionFile[AnyDefinition]]:
        """Return an iterator over the definition files in the repository."""
        yield from self._contents.values()

    def paths(self) -> Iterable[RepoPath]:
        """Return an iterator over the paths in the repository."""
        yield from self._contents.keys()

    def extensions(self) -> Iterable[str]:
        """Return an iterator over the extension directories in the repository.

        Be warned: an extension directory may not match the name of the extension in `extension.json`.
        """
        extns: set[str] = set()
        for path in self._contents:
            if path.startswith(RepoPaths.EXTENSIONS.value):
                extns.add(PurePath(path).parts[1])
        yield from extns

    def profiles(self) -> Iterable[str]:
        """Return an iterator over the profile names in the repository."""
        for path in self._contents:
            parts = PurePath(path).parts
            match parts:
                case (RepoPaths.EXTENSIONS, _, RepoPaths.PROFILES.value, _) | (RepoPaths.PROFILES.value, _):
                    data = self._contents[path].data
                    if isinstance(data, ProfileDefn) and isinstance(data.name, str):
                        yield data.name
                    else:
                        yield PurePath(path).stem
                case _:
                    pass

    def narrow(self, path: RepoPath, kind: type[DefnT]) -> DefinitionFile[DefnT]:
        """Return the definition file at path as the requested kind.

        This ensures that the `data` attribute of the file matches the requested
        kind. It is useful for type narrowing.
        """
        val = self[path]
        try:
            assert isinstance(val.data, kind)
            assert path_defn_t(path) == kind
        except AssertionError:
            raise TypeError(f"Expected {kind} at {path}, got {type(val.data)}")
        return cast(DefinitionFile[DefnT], val)
