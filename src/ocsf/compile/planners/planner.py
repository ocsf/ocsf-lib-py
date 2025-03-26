from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ocsf.repository import AnyDefinition, DefinitionFile, RepoPath

from ..merge import MergeResult
from ..options import CompilationOptions
from ..protoschema import ProtoSchema


@dataclass(eq=True, frozen=True)
class Operation(ABC):
    target: RepoPath
    prerequisite: Optional[RepoPath] = None

    @abstractmethod
    def apply(self, schema: ProtoSchema) -> MergeResult: ...


Analysis = Operation | list[Operation] | None


class Planner(ABC):
    def __init__(self, schema: ProtoSchema, options: CompilationOptions):
        self._schema = schema
        self._options = options

    @abstractmethod
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis: ...
