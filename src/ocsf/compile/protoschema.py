import dacite

from copy import deepcopy
from dataclasses import asdict
from pathlib import PurePath
from typing import Any, cast, TypeVar

from ocsf.schema import OcsfSchema, OcsfObject, OcsfEvent, OcsfType, OcsfProfile, OcsfExtension
from ocsf.repository import (
    Repository,
    ObjectDefn,
    EventDefn,
    SpecialFiles,
    TypeDefn,
    ExtensionDefn,
    ProfileDefn,
    DictionaryDefn,
    AnyDefinition,
    VersionDefn,
    DefinitionFile,
    DefinitionData,
    RepoPath,
    RepoPaths,
    as_path,
    extension,
)


DefnT = TypeVar("DefnT", bound=DefinitionData)


def _remove_nones(data: dict[str, Any]) -> None:
    rm: list[str] = []
    for k, v in data.items():
        if v is None:
            rm.append(k)
        elif isinstance(v, dict):
            v = cast(dict[str, Any], v)
            # No need to update data[k] b/c v is a reference to data[k]
            _remove_nones(v)

    for k in rm:
        del data[k]


class ProtoSchema:
    def __init__(self, repo: Repository):
        self.repo = repo
        self._files: dict[RepoPath, DefinitionFile[AnyDefinition]] = {}

    def __getitem__(self, path: RepoPath) -> DefinitionFile[AnyDefinition]:
        if path not in self._files:
            if path in self.repo:
                self._files[path] = deepcopy(self.repo[path])
            else:
                raise KeyError(f"File {path} not found in repository")
        return self._files[path]

    def __setitem__(self, path: RepoPath, file: DefinitionFile[AnyDefinition]) -> None:
        # value = deepcopy(value)
        file.path = path
        self._files[path] = file

    def object_path(self, name: str) -> RepoPath:
        return as_path(RepoPaths.OBJECTS.value, name, ".json")

    def event_path(self, name: str) -> RepoPath:
        default = as_path(RepoPaths.EVENTS.value, name, ".json")
        if default not in self.repo:
            for file in self.repo.files():
                if file.path.startswith(RepoPaths.EVENTS.value):
                    if file.short_name() == name:
                        return file.path
        return default

    def profile_path(self, name: str) -> RepoPath:
        return as_path(RepoPaths.PROFILES.value, name, ".json")

    def find_object(self, name: str) -> DefinitionFile[ObjectDefn]:
        found: list[str] = []
        for file in self._files.values():
            if file.path.startswith(RepoPaths.OBJECTS.value) and file.data is not None:
                assert isinstance(file.data, ObjectDefn)
                if file.data.get_key() == name or file.data.name == name:
                    found.append(file.path)

        if len(found) == 0:
            raise KeyError(f"Object {name} not found")

        path = sorted(found, key=lambda x: len(x))[0]
        return cast(DefinitionFile[ObjectDefn], self.__getitem__(path))

    def find_event(self, name: str) -> DefinitionFile[EventDefn]:
        found: list[str] = []
        for file in self._files.values():
            if file.path.startswith(RepoPaths.EVENTS.value) and file.data is not None:
                assert isinstance(file.data, EventDefn)
                if file.data.get_key() == name or file.data.name == name:
                    found.append(file.path)

        if len(found) == 0:
            raise KeyError(f"Event {name} not found")

        path = sorted(found, key=lambda x: len(x))[0]
        return cast(DefinitionFile[EventDefn], self.__getitem__(path))

    def find_extension_path(self, name: str) -> str:
        test = as_path(RepoPaths.EXTENSIONS.value, name, SpecialFiles.EXTENSION)
        if test in self.repo:
            return as_path(RepoPaths.EXTENSIONS.value, name)

        for path in self.repo.paths():
            file = self[path]
            assert file.path is not None
            parts = PurePath(file.path).parts

            match parts:
                case (RepoPaths.EXTENSIONS.value, extn, SpecialFiles.EXTENSION):
                    assert isinstance(file.data, ExtensionDefn)
                    assert file.data.name is not None
                    if file.data.name == name:
                        return as_path(RepoPaths.EXTENSIONS.value, extn)
                case _:
                    pass

        raise KeyError(f"Extension {name} not found")

    def schema(self) -> OcsfSchema:
        schema = OcsfSchema(version="0.0.0")  # Version updated below

        for file in self._files.values():
            try:
                if file.path.startswith(RepoPaths.OBJECTS.value) and not extension(file.path):
                    assert file.data is not None
                    assert isinstance(file.data, ObjectDefn)
                    key = file.data.get_key()
                    assert key is not None
                    if not key.startswith("_"):
                        data = asdict(file.data)
                        _remove_nones(data)
                        schema.objects[key] = dacite.from_dict(OcsfObject, data)

                elif file.path.startswith(RepoPaths.EVENTS.value):
                    assert file.data is not None
                    assert isinstance(file.data, EventDefn)
                    if file.data.uid is not None or file.data.name == "base_event":
                        key = file.data.get_key()
                        assert key is not None
                        data = asdict(file.data)
                        _remove_nones(data)
                        schema.classes[key] = dacite.from_dict(OcsfEvent, data)

                elif file.path.startswith(RepoPaths.PROFILES.value):
                    assert file.data is not None
                    assert isinstance(file.data, ProfileDefn)
                    data = asdict(file.data)
                    _remove_nones(data)
                    if schema.profiles is None:
                        schema.profiles = {}
                    key = file.data.get_key()
                    assert key is not None
                    schema.profiles[key] = dacite.from_dict(OcsfProfile, data)

                elif file.path.endswith(SpecialFiles.EXTENSION.value):
                    assert file.data is not None
                    assert isinstance(file.data, ExtensionDefn)
                    assert file.data.name is not None
                    data = asdict(file.data)
                    _remove_nones(data)
                    if schema.extensions is None:
                        schema.extensions = {}
                    schema.extensions[file.data.name] = dacite.from_dict(OcsfExtension, data)

                elif file.path == SpecialFiles.DICTIONARY:
                    assert file.data is not None
                    assert isinstance(file.data, DictionaryDefn)
                    assert file.data.types is not None
                    assert isinstance(file.data.types.attributes, dict)
                    for k, v in file.data.types.attributes.items():
                        if isinstance(v, TypeDefn):
                            data = asdict(v)
                            _remove_nones(data)
                            schema.types[k] = dacite.from_dict(OcsfType, data)

                elif file.path == SpecialFiles.VERSION:
                    assert file.data is not None
                    assert isinstance(file.data, VersionDefn)
                    assert file.data.version is not None
                    schema.version = file.data.version

            except Exception as e:
                raise ValueError(f"Error processing {file.path}: {e}") from e

        if "base" in schema.classes:
            schema.base_event = schema.classes["base"]

        return schema
