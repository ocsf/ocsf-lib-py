from copy import deepcopy
from dataclasses import dataclass

from ocsf.repository import DefinitionFile, DefnWithAttrs, AttrDefn, AnyDefinition
from ..merge import MergeResult
from ..protoschema import ProtoSchema
from .planner import Operation, Planner, Analysis


@dataclass(eq=True, frozen=True)
class DateTimeOp(Operation):
    """Append the category and class names to the description of the category_name and class_name attributes."""

    def apply(self, schema: ProtoSchema) -> MergeResult:
        data = schema[self.target].data
        assert isinstance(data, DefnWithAttrs)

        results: MergeResult = []
        if data.attributes is not None:
            append: dict[str, AttrDefn] = {}
            for name, attr in data.attributes.items():
                if isinstance(attr, AttrDefn) and attr.type == "timestamp_t":
                    dt = deepcopy(attr)
                    dt.type = "datetime_t"
                    dt.profile = "datetime"
                    dt.requirement = "optional"
                    append[name + "_dt"] = dt

            for name, attr in append.items():
                data.attributes[name] = attr
                results.append(("attributes", name))

        return results


class DateTimePlanner(Planner):
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        # TODO check that datetime profile is enabled
        if self._options.profiles is None or "datetime" in self._options.profiles:
            data = self._schema[input.path].data
            if isinstance(data, DefnWithAttrs):
                return DateTimeOp(input.path)
