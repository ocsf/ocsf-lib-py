from dataclasses import dataclass
from pathlib import PurePath
from typing import Optional

from ..protoschema import ProtoSchema
from ..merge import merge, MergeResult, FieldList
from .planner import Operation, Planner, Analysis

from ocsf.repository import (
    DefinitionFile,
    DefnWithInclude,
    DefnWithAttrs,
    Repository,
    AnyDefinition,
    RepoPath,
    extension,
    extensionless,
    as_path,
)


@dataclass(eq=True, frozen=True)
class IncludeOp(Operation):
    in_attrs: bool = False

    def __str__(self):
        return f"Include {self.target} <- {self.prerequisite}"

    def apply(self, schema: ProtoSchema) -> MergeResult:
        target = schema[self.target]
        assert target.data is not None

        assert self.prerequisite is not None
        prereq = schema[self.prerequisite]
        assert prereq.data is not None

        allowed: FieldList | None = ["attributes"] if self.in_attrs else None
        return merge(target.data, prereq.data, allowed_fields=allowed)


def _find_dependency(repo: Repository, subject: str, relative_to: Optional[RepoPath] = None) -> RepoPath | None:
    """Find the target of an $include directive relative to its source file.

    Arguments:
        subject: The subject to locate as it is described in the directive. It may be a filepath, an object name, etc.
        relative_to: The file containing (or implying) the directive instruction.

    Returns: A filepath in the Repository that references the source file.
    """

    subj_path = PurePath(subject)
    files: list[str] = [subject]
    if subj_path.suffix != ".json":
        files.append(subject + ".json")

    paths: list[PurePath] = []

    if relative_to is not None:
        paths.append(PurePath(relative_to))

        if extension(relative_to) is not None:
            paths.append(PurePath(extensionless(relative_to)))

    for entry in paths:
        for path in [entry] + list(entry.parents):
            for file in files:
                k = as_path(path, file)
                if k in repo:
                    return k

    return None


class IncludePlanner(Planner):
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        if input.data is not None:
            found: list[Operation] = []
            if isinstance(input.data, DefnWithInclude):
                if input.data.include_ is not None:
                    if isinstance(input.data.include_, str):
                        includes = [input.data.include_]
                    else:
                        includes = input.data.include_

                    input.data.include_ = None

                    for include in includes:
                        location = _find_dependency(self._schema.repo, include, input.path)
                        if location is not None:
                            found.append(IncludeOp(input.path, location))

            if isinstance(input.data, DefnWithAttrs):
                if input.data.attributes is not None and "include_" in input.data.attributes:
                    includes = input.data.attributes["include_"]

                    if isinstance(includes, str):
                        includes = [includes]
                    else:
                        assert isinstance(includes, list)

                    for include in includes:
                        location = _find_dependency(self._schema.repo, include, input.path)
                        if location is not None:
                            found.append(IncludeOp(input.path, location, in_attrs=True))

                    del input.data.attributes["include_"]

            return found
