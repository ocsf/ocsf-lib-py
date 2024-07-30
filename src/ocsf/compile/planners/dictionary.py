from dataclasses import dataclass

from ..protoschema import ProtoSchema
from ..merge import merge, MergeResult

from .planner import Operation, Planner, Analysis
from ocsf.repository import DefinitionFile, AnyDefinition, SpecialFiles, DictionaryDefn, AttrDefn, DefnWithAttrs


@dataclass(eq=True, frozen=True)
class DictionaryOp(Operation):
    def __str__(self):
        return f"Dictionary {self.target} <- {self.prerequisite}"

    def apply(self, schema: ProtoSchema) -> MergeResult:
        target = schema[self.target]
        # assert target.data is not None
        assert isinstance(target.data, DefnWithAttrs)
        if target.data.attributes is None:
            return []

        assert self.prerequisite is not None
        prereq = schema[self.prerequisite]
        assert prereq.data is not None
        assert isinstance(prereq.data, DictionaryDefn)
        if prereq.data.attributes is None:
            return []

        # Merge each attribute below.
        # We could merge the event with the dictionary, set allowed fields to
        # ["attributes"], and add_dict_items to False. That would limit the
        # merge to the attributes section of the dictionary and prevent adding
        # all attributes to the event. However, it will also prevent enum
        # members defined in dictionary.json from being merged to events.
        results: MergeResult = []
        for key, value in target.data.attributes.items():
            if isinstance(value, AttrDefn) and key in prereq.data.attributes:
                right = prereq.data.attributes[key]
                assert isinstance(right, AttrDefn)
                rs = merge(value, right)
                for r in rs:
                    results.append(("attributes", key) + r)

        return results


class DictionaryPlanner(Planner):
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        if input.data is not None:
            if isinstance(input.data, DefnWithAttrs):
                return DictionaryOp(input.path, SpecialFiles.DICTIONARY.value)
