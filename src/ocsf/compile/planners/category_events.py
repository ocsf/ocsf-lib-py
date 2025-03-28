from copy import copy
from dataclasses import dataclass

from ocsf.repository import AnyDefinition, CategoriesDefn, CategoryDefn, DefinitionFile, EventDefn, SpecialFiles

from ..merge import MergeResult
from ..options import CompilationOptions
from ..protoschema import ProtoSchema
from .planner import Analysis, Operation, Planner


@dataclass(eq=True, frozen=True)
class MapEventToCategoryOp(Operation):
    def apply(self, schema: ProtoSchema) -> MergeResult:
        # Retrieve event definition
        assert self.prerequisite is not None
        prereq = schema[self.prerequisite].data
        assert isinstance(prereq, EventDefn)
        event_key = prereq.get_key()

        if prereq.category is None or prereq.uid is None or event_key is None:
            return []

        # Retrieve target (categories.json)
        target = schema[self.target].data
        assert isinstance(target, CategoriesDefn)
        if target.attributes is None:
            return []

        # The category /should/ exist, but some events reference an 'other'
        # category that is not listed.
        if prereq.category not in target.attributes:
            return []

        cat = target.attributes[prereq.category]
        assert isinstance(cat, CategoryDefn)
        if cat.classes is None:
            cat.classes = {}

        # We don't want the attributes in the event definition here, so we copy
        # the event and remove them.
        event = copy(prereq)
        event.attributes = None

        cat.classes[event_key] = event

        return [("attributes", "classes", prereq.category, event_key)]

    def __str__(self):
        return f"Map event to category {self.target} <- {self.prerequisite}"


class MapEventToCategoryPlanner(Planner):
    def __init__(self, schema: ProtoSchema, options: CompilationOptions):
        super().__init__(schema, options)

    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        if self._options.map_events_to_categories is False:
            return []

        if isinstance(input.data, EventDefn):
            return MapEventToCategoryOp(target=SpecialFiles.CATEGORIES, prerequisite=input.path)
