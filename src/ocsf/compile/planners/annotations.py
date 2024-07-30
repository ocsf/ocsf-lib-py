from dataclasses import dataclass

from .planner import Operation, Planner, Analysis
from ..merge import merge, MergeResult, MergeOptions
from ..protoschema import ProtoSchema

from ocsf.repository import DefinitionFile, DefnWithAnnotations, AttrDefn, AnyDefinition


@dataclass(eq=True, frozen=True)
class AnnotationOp(Operation):
    def __str__(self):
        return f"Expand annotations in {self.target}"

    def apply(self, schema: ProtoSchema) -> MergeResult:
        target = schema[self.target]
        assert target.data is not None
        assert isinstance(target.data, DefnWithAnnotations)

        if target.data.annotations is None or target.data.attributes is None:
            return []

        results: MergeResult = []
        for name, attr in target.data.attributes.items():
            if isinstance(attr, AttrDefn):
                for result in merge(
                    attr, target.data.annotations, options=MergeOptions(overwrite=True, overwrite_none=False)
                ):
                    results.append(("attributes", name) + result)

        return results


class AnnotationPlanner(Planner):
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        if input.data is not None and isinstance(input.data, DefnWithAnnotations):
            return AnnotationOp(target=input.path)
