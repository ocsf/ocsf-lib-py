from dataclasses import dataclass
from typing import Optional

from ..protoschema import ProtoSchema
from ..merge import MergeResult
from ..options import CompilationOptions

from .planner import Operation, Planner, Analysis
from ocsf.repository import DefinitionFile, EventDefn, ObjectDefn, AttrDefn, DefnWithAttrs, AnyDefinition


class _Types:
    def __init__(self, schema: ProtoSchema):
        self._schema = schema
        self._objects: dict[str, str | None] = {}
        self._events: dict[str, str | None] = {}
        self._built = False

    def _build(self):
        if self._built:
            return True

        for defn in self._schema.repo.files():
            if isinstance(defn.data, ObjectDefn) and defn.data.name is not None:
                self._objects[defn.data.name] = defn.data.caption
            elif isinstance(defn.data, EventDefn) and defn.data.name is not None:
                self._events[defn.data.name] = defn.data.caption

        self._built = True

    def objects(self) -> dict[str, str | None]:
        if not self._built:
            self._build()
        return self._objects

    def events(self) -> dict[str, str | None]:
        if not self._built:
            self._build()
        return self._events


@dataclass(eq=True, frozen=True)
class ObjectTypeOp(Operation):
    types: Optional[_Types] = None

    def __str__(self):
        return f"SetObjectType {self.target}"

    def apply(self, schema: ProtoSchema) -> MergeResult:
        assert self.types is not None

        data = schema[self.target].data
        assert isinstance(data, DefnWithAttrs)

        objects = self.types.objects()
        events = self.types.events()

        results: MergeResult = []
        if data.attributes is not None:
            for name, attr in data.attributes.items():
                if isinstance(attr, AttrDefn) and attr.type is not None:
                    if attr.type[:-2] == "_t":
                        if attr.type in objects:
                            attr.object_type = attr.type
                            attr.object_name = objects[attr.type]
                            attr.type = "object"
                        elif attr.type in events:
                            attr.object_type = attr.type
                            attr.object_name = events[attr.type]
                            attr.type = "event"
                        else:
                            raise ValueError(f"Unknown object type {attr.type}")

                        results.append(("attributes", name, "type"))
                        results.append(("attributes", name, "object_type"))
                        results.append(("attributes", name, "object_name"))

        return results


class ObjectTypePlanner(Planner):
    def __init__(self, schema: ProtoSchema, options: CompilationOptions):
        super().__init__(schema, options)
        self._types = _Types(schema)

    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        if self._options.set_object_types is False:
            return []

        if input.data is not None:
            if isinstance(input.data, DefnWithAttrs):
                return ObjectTypeOp(input.path, types=self._types)
