from abc import ABC
from dataclasses import dataclass
from typing import Optional

from ocsf.repository import DefinitionFile, RepoPath, AnyDefinition

from ..protoschema import ProtoSchema
from ..options import CompilationOptions
from ..merge import MergeResult


@dataclass(eq=True, frozen=True)
class Operation(ABC):
    target: RepoPath
    prerequisite: Optional[RepoPath] = None

    def apply(self, schema: ProtoSchema) -> MergeResult:
        raise NotImplementedError()


Analysis = Operation | list[Operation] | None


class Planner(ABC):
    def __init__(self, schema: ProtoSchema, options: CompilationOptions):
        self._schema = schema
        self._options = options

    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        raise NotImplementedError()
