from dataclasses import dataclass
from pathlib import PurePath

from ..protoschema import ProtoSchema
from ..merge import merge, MergeResult
from .planner import Operation, Planner, Analysis
from ocsf.repository import (
    RepoPaths,
    ObjectDefn,
    EventDefn,
    extension,
    extensionless,
    DefinitionFile,
    AnyDefinition,
    Repository,
    RepoPath,
    as_path,
)


def _find_base(repo: Repository, subject: str, relative_to: RepoPath) -> RepoPath | None:
    rel_path = PurePath(relative_to)

    try:
        idx = rel_path.parts.index(RepoPaths.OBJECTS.value)
    except ValueError:
        idx = rel_path.parts.index(RepoPaths.EVENTS.value)
    prefix = as_path(*rel_path.parts[: idx + 1])

    for file in repo.files():
        if file.path.startswith(prefix):
            subj_path = PurePath(file.path)
            if subj_path.stem == subject:
                return file.path
            elif isinstance(file.data, ObjectDefn) or isinstance(file.data, EventDefn):
                if file.data.name is not None and file.data.name == subject:
                    return file.path

    if extension(relative_to) is not None:
        return _find_base(repo, subject, extensionless(relative_to))

    return None


@dataclass(eq=True, frozen=True)
class ExtendsOp(Operation):
    def __str__(self):
        return f"Extends {self.target} <- {self.prerequisite}"

    def apply(self, schema: ProtoSchema) -> MergeResult:
        target = schema[self.target]
        assert target.data is not None

        assert self.prerequisite is not None
        prereq = schema[self.prerequisite]
        assert prereq.data is not None

        return merge(target.data, prereq.data)


class ExtendsPlanner(Planner):
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        if input.data is not None:
            if isinstance(input.data, ObjectDefn) or isinstance(input.data, EventDefn):
                if input.data.extends is not None:
                    location = _find_base(self._schema.repo, input.data.extends, input.path)
                    if location is not None:
                        return ExtendsOp(input.path, location)
