from dataclasses import dataclass
from pathlib import PurePath

from ocsf.repository import AnyDefinition, CategoriesDefn, DefinitionFile, EventDefn, RepoPaths, SpecialFiles

from ..merge import MergeResult
from ..protoschema import ProtoSchema
from .planner import Analysis, Operation, Planner


@dataclass(eq=True, frozen=True)
class SetCategoryOp(Operation):
    def __str__(self):
        return f"Assign category to {self.target}"

    def apply(self, schema: ProtoSchema) -> MergeResult:
        target = schema[self.target]
        assert isinstance(target.data, EventDefn)

        if target.data.category is not None:
            return []

        path = PurePath(target.path).parts
        if path[-1] == SpecialFiles.BASE_EVENT.value:
            return []

        if RepoPaths.EVENTS.value not in path:
            raise ValueError(f"Cannot assign category to non-event: {target.path}")
            return []

        category = path[path.index(RepoPaths.EVENTS.value) + 1]
        if category == "base_event.json":
            return []

        categories = schema[SpecialFiles.CATEGORIES].data
        assert isinstance(categories, CategoriesDefn)
        if not isinstance(categories.attributes, dict):
            raise ValueError("categories.json file is missing attributes")

        if category not in categories.attributes:
            raise ValueError(f"Unknown category: {category}")

        target.data.category = category
        return [("category",)]


class SetCategoryPlanner(Planner):
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        if input.data is not None and isinstance(input.data, EventDefn) and input.data.category is None:
            return SetCategoryOp(target=input.path, prerequisite=SpecialFiles.CATEGORIES)
