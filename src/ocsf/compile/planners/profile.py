"""Profile planner and operations for OCSF compiler.

Profiles are defined in separate files and add attributes to objects and events.


"""

from dataclasses import dataclass
from pathlib import PurePath

from ..protoschema import ProtoSchema
from ..options import CompilationOptions
from ..merge import MergeResult
from .planner import Operation, Planner, Analysis
from ocsf.repository import (
    DefinitionFile,
    ProfileDefn,
    ObjectDefn,
    EventDefn,
    as_path,
    extension,
    RepoPaths,
    AttrDefn,
    AnyDefinition,
)


@dataclass(eq=True, frozen=True)
class ExcludeProfileAttrsOp(Operation):
    def apply(self, schema: ProtoSchema) -> MergeResult:
        result: MergeResult = []

        assert self.prerequisite is not None

        target = schema[self.target]
        assert target.data is not None
        assert isinstance(target.data, ObjectDefn) or isinstance(target.data, EventDefn)

        if target.data.attributes is None:
            return result

        profile = schema[self.prerequisite]
        assert profile.data is not None
        assert isinstance(profile.data, ProfileDefn)

        if profile.data.attributes is not None:
            for attr in profile.data.attributes:
                if attr in target.data.attributes:
                    result.append(("attributes", attr))
                    del target.data.attributes[attr]

        return result

    def __str__(self):
        return f"Exclude Profile {self.target} <- {self.prerequisite}"


@dataclass(eq=True, frozen=True)
class MarkProfileOp(Operation):
    def apply(self, schema: ProtoSchema) -> MergeResult:
        result: MergeResult = []

        assert self.prerequisite is None

        target = schema[self.target]
        assert target.data is not None
        assert isinstance(target.data, ProfileDefn)

        if target.data.attributes is None:
            return result

        if target.data.name is None:
            raise ValueError(f"Profile name is required {self.target}")

        for name, attr in target.data.attributes.items():
            if isinstance(attr, AttrDefn):
                result.append(("attributes", name, "profile"))
                attr.profile = target.data.name

        return result

    def __str__(self):
        return f"Mark Profile {self.target} <- {self.prerequisite}"


def _find_profile(schema: ProtoSchema, profile_ref: str, relative_to: str) -> str | None:
    # extn/profile_name
    # profiles/profile_name.json
    # <extn>/profiles/profile_name.json

    profile_name = PurePath(profile_ref).stem
    search = [profile_ref, as_path(RepoPaths.PROFILES, profile_name + ".json")]

    extn = extension(relative_to)
    if extn is not None:
        search.append(as_path(RepoPaths.EXTENSIONS, extn, RepoPaths.PROFILES, profile_name + ".json"))

    parts = PurePath(profile_ref).parts
    if len(parts) > 1:
        try:
            path = schema.find_extension_path(parts[0])
            search.append(as_path(path, RepoPaths.PROFILES, profile_name + ".json"))
        except KeyError:
            pass

    for path in reversed(search):
        if path in schema.repo:
            return path

    return None


class ExcludeProfileAttrsPlanner(Planner):
    def __init__(self, schema: ProtoSchema, options: CompilationOptions):
        if options.profiles is None:
            options.profiles = list(schema.repo.profiles())

        if options.ignore_profiles is not None:
            options.profiles = [prof for prof in options.profiles if prof not in options.ignore_profiles]

        super().__init__(schema, options)

    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        assert self._options.profiles is not None

        if isinstance(input.data, ObjectDefn) or isinstance(input.data, EventDefn):
            if input.data.profiles is not None:
                # profile_ref will be in one of the following formats:
                #   extension/profile_name
                #   profiles/profile_name
                #   profiles/profile_name.json
                for profile_ref in input.data.profiles:
                    path = _find_profile(self._schema, profile_ref, input.path)
                    if path is not None and PurePath(profile_ref).stem not in self._options.profiles:
                        return ExcludeProfileAttrsOp(input.path, path)

        return None


class MarkProfilePlanner(ExcludeProfileAttrsPlanner):
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        assert self._options.profiles is not None

        if isinstance(input.data, ProfileDefn):
            return MarkProfileOp(input.path, None)
