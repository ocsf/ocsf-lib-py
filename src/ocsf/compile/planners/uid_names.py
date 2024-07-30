from dataclasses import dataclass

from ocsf.repository import DefinitionFile, EventDefn, AttrDefn, AnyDefinition
from ..merge import MergeResult
from ..protoschema import ProtoSchema
from .planner import Operation, Planner, Analysis

# prepend category_name and class_name caption


@dataclass(eq=True, frozen=True)
class UidSiblingOp(Operation):
    """Append the category and class names to the description of the category_name and class_name attributes."""

    def apply(self, schema: ProtoSchema) -> MergeResult:
        data = schema[self.target].data
        assert isinstance(data, EventDefn)

        results: MergeResult = []
        if data.attributes is not None:
            if data.name != "base_event" and "category_uid" in data.attributes and "category_name" in data.attributes:
                assert isinstance(data.attributes["category_uid"], AttrDefn)
                assert isinstance(data.attributes["category_uid"].enum, dict)
                cat = list(data.attributes["category_uid"].enum.values())[0]

                assert isinstance(data.attributes["category_name"], AttrDefn)
                assert data.attributes["category_name"].description is not None
                data.attributes["category_name"].description = (
                    data.attributes["category_name"].description[:-1] + f": <code>{cat.caption}</code>."
                )
                results.append(("attributes", "category_name", "description"))

            if "class_uid" in data.attributes and "class_name" in data.attributes:
                assert isinstance(data.attributes["class_uid"], AttrDefn)
                assert isinstance(data.attributes["class_uid"].enum, dict)
                cls = list(data.attributes["class_uid"].enum.values())[0]

                assert isinstance(data.attributes["class_name"], AttrDefn)
                assert data.attributes["class_name"].description is not None
                data.attributes["class_name"].description = (
                    data.attributes["class_name"].description[:-1] + f": <code>{cls.caption}</code>."
                )
                results.append(("attributes", "class_name", "description"))

        return results


class UidSiblingPlanner(Planner):
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        data = self._schema[input.path].data
        if isinstance(data, EventDefn):
            return UidSiblingOp(input.path)
