from dataclasses import dataclass
from pathlib import PurePath

from .planner import Operation, Planner, Analysis
from ..merge import MergeResult
from ..protoschema import ProtoSchema

from ocsf.repository import DefinitionFile, EventDefn, SpecialFiles, RepoPaths, CategoriesDefn, AnyDefinition


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
        if RepoPaths.EVENTS.value not in path:
            raise ValueError(f"Cannot assign category to non-event: {target.path}")
            return []

        category = path[path.index(RepoPaths.EVENTS.value) + 1]

        categories = schema[SpecialFiles.CATEGORIES].data
        assert isinstance(categories, CategoriesDefn)
        if not isinstance(categories.attributes, dict):
            raise ValueError("categories.json file is missing attributes")

        if category not in categories.attributes:
            raise ValueError(f"Unknown category: {category}")
            return []

        target.data.category = category
        return [("category",)]


class SetCategoryPlanner(Planner):
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        if input.data is not None and isinstance(input.data, EventDefn) and input.data.category is None:
            return SetCategoryOp(target=input.path, prerequisite=SpecialFiles.CATEGORIES)
