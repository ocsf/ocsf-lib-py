"""Observable planners and operations.

Mark Observables
================
Assign the observable value to attributes in the compiled schema output based
on type and attribute name.

This will set the observable ID on all attributes with a type that has an
observable Type ID in the dictionary.json file or an attribute by the same name
with an observable ID in the dictionary.json file.

Producers and consumers wishing to build the observables attribute of records
can use this observable property to do so rather than implementing their own
logic to determine the correct observable type_id of attributes.

Build Observable Types
======================
Build the observable type_id enum based on values found in dictionary.json and
across objects and events.
"""

from dataclasses import dataclass
from typing import Optional

from ocsf.repository import (
    AnyDefinition,
    AttrDefn,
    DefinitionFile,
    DefnWithAttrs,
    DictionaryDefn,
    DictionaryTypesDefn,
    EnumMemberDefn,
    EventDefn,
    ObjectDefn,
    SpecialFiles,
    TypeDefn,
)

from ..merge import MergeResult
from ..options import CompilationOptions
from ..protoschema import ProtoSchema
from .planner import Analysis, Operation, Planner


class _Registry:
    """A registry of observable attributes and types from the dictionary.json
    file so that the mapping can be computed once across all operations.
    """

    def __init__(self, schema: ProtoSchema):
        self._schema = schema
        self._types: Optional[dict[str, int]] = None
        self._attrs: Optional[dict[str, int]] = None
        self._objects: dict[str, int | None] = {}

    def _build(self):
        if self._types is not None or self._attrs is not None:
            return
        types = {}
        attrs = {}

        if SpecialFiles.DICTIONARY not in self._schema.repo:
            raise ValueError("Missing dictionary.json file")

        dictionary = self._schema[SpecialFiles.DICTIONARY].data
        assert isinstance(dictionary, DictionaryDefn)

        if dictionary.attributes is not None:
            for k, v in dictionary.attributes.items():
                if isinstance(v, AttrDefn):
                    if v.observable is not None:
                        attrs[k] = v.observable

        if isinstance(dictionary.types, DictionaryTypesDefn) and dictionary.types.attributes is not None:
            for k, v in dictionary.types.attributes.items():
                if isinstance(v, TypeDefn):
                    if v.observable is not None:
                        types[k] = v.observable

        self._types = types
        self._attrs = attrs

    def types(self) -> dict[str, int]:
        if self._types is None:
            self._build()
        assert self._types is not None
        return self._types

    def attrs(self) -> dict[str, int]:
        if self._attrs is None:
            self._build()
        assert self._attrs is not None
        return self._attrs

    def find_object(self, name: str) -> int | None:
        if name not in self._objects:
            try:
                defn = self._schema.find_object(name)
                if defn.data is not None and defn.data.observable:
                    self._objects[name] = defn.data.observable
                else:
                    self._objects[name] = None
            except KeyError:
                self._objects[name] = None
        return self._objects[name]


@dataclass(eq=True, frozen=True)
class MarkObservablesOp(Operation):
    registry: Optional[_Registry] = None

    def __str__(self):
        return f"Mark observable property of attributes in {self.target}"

    def apply(self, schema: ProtoSchema) -> MergeResult:
        assert self.registry is not None

        data = schema[self.target].data
        assert isinstance(data, DefnWithAttrs)

        attrs = self.registry.attrs()
        types = self.registry.types()

        results: MergeResult = []
        if data.attributes is not None:
            for name, attr in data.attributes.items():
                if isinstance(attr, AttrDefn):
                    # Observable by dictionary attribute name
                    if name in attrs:
                        attr.observable = attrs[name]
                        results.append(("attributes", name, "observable"))

                    # Observable by primitive dictionary type
                    elif attr.type in types:
                        attr.observable = types[attr.type]
                        results.append(("attributes", name, "observable"))

                    # Observable by object type
                    else:
                        # The OCSF server sets type to "object" and assigns the
                        # object name to object_type.
                        if attr.type == "object" and attr.object_type is not None:
                            obs_id = self.registry.find_object(attr.object_type)

                        # Some other implementations (OK, they're all mine) set
                        # type to the object name.
                        elif attr.type is not None:
                            obs_id = self.registry.find_object(attr.type)

                        else:
                            obs_id = None

                        if obs_id is not None:
                            attr.observable = obs_id
                            results.append(("attributes", name, "observable"))

        return results


@dataclass(eq=True, frozen=True)
class BuildObservableTypeOp(Operation):
    registry: Optional[_Registry] = None

    def __str__(self):
        return f"Build observable types from in {self.prerequisite}"

    def apply(self, schema: ProtoSchema) -> MergeResult:
        if self.prerequisite is None:
            raise ValueError("Prerequisite is required")

        target = schema[self.target].data
        assert isinstance(target, ObjectDefn)
        assert target.attributes is not None
        assert "type_id" in target.attributes
        assert isinstance(target.attributes["type_id"], AttrDefn)
        enum = target.attributes["type_id"].enum
        assert enum is not None

        results: MergeResult = []
        data = schema[self.prerequisite].data

        if self.prerequisite == SpecialFiles.DICTIONARY:
            assert self.registry is not None
            assert isinstance(data, DictionaryDefn)

            # Dictionary attribute observables
            assert isinstance(data.attributes, dict)
            attrs = self.registry.attrs()
            for key in attrs:
                enum_id = str(attrs[key])
                attr = data.attributes[key]
                assert isinstance(attr, AttrDefn)
                enum[enum_id] = EnumMemberDefn(
                    caption=attr.caption, description=f"Observable by Dictionary Attribute.<br>{attr.description}"
                )
                results.append(("attributes", "type_id", "enum", enum_id))

            # Dictionary type observables
            assert isinstance(data.types, DictionaryTypesDefn)
            assert isinstance(data.types.attributes, dict)

            types = self.registry.types()
            for key in types:
                enum_id = str(types[key])
                type_ = data.types.attributes[key]
                assert isinstance(type_, TypeDefn)
                enum[enum_id] = EnumMemberDefn(
                    caption=type_.caption, description=f"Observable by Dictionary Type.<br>{type_.description}"
                )
                results.append(("attributes", "type_id", "enum", enum_id))

        elif isinstance(data, EventDefn) or isinstance(data, ObjectDefn):
            if isinstance(data, ObjectDefn) and data.observable is not None:
                obj = self.prerequisite
                obj_data = data
                while (base := schema.find_base(obj)) is not None:
                    base_data = schema[base].data
                    obj = base
                    if isinstance(base_data, ObjectDefn) and base_data.observable is not None:
                        obj_data = base_data

                # Object observable
                enum_id = str(obj_data.observable)
                if enum_id not in enum:
                    enum[enum_id] = EnumMemberDefn(
                        caption=obj_data.caption, description=f"Observable by Object.<br>{obj_data.description}"
                    )
                    results.append(("attributes", "type_id", "enum", enum_id))

            if isinstance(data.attributes, dict):
                # Object/Event attribute observable
                label = "Event" if isinstance(data, EventDefn) else "Object"
                for k, v in data.attributes.items():
                    if isinstance(v, AttrDefn) and v.observable is not None:
                        enum_id = str(v.observable)
                        if enum_id not in enum:  # Don't overwrite enum values defined in dictionary.json
                            # Walk up the schema to find the base object or
                            # event that introduced the observable.
                            #
                            # In the case of Resource Details and Databucket
                            # Object, the observable enum member caption should
                            # be derived from the former, but the latter is
                            # processed first. So we walk up the "inheritance" tree
                            # to find the first base object or event that
                            # introduced this attribute with an `observable`
                            # marker to derive the caption.
                            obj = self.prerequisite
                            while (base := schema.find_base(obj)) is not None:
                                base_data = schema[base].data
                                obj = base
                                if isinstance(base_data, ObjectDefn) or isinstance(base_data, EventDefn):
                                    if (
                                        base_data.attributes
                                        and k in base_data.attributes
                                        and isinstance(attr := base_data.attributes[k], AttrDefn)
                                        and attr.observable is not None
                                    ):
                                        data = base_data

                            # Build the enum member for the observable
                            enum[enum_id] = EnumMemberDefn(
                                caption=f"{data.caption} {label}: {k}",
                                description=(
                                    f"Observable by {label}-Specific Attribute.<br>{label}-specific "
                                    f'attribute "{k}" for the {data.caption} {label}.'
                                ),
                            )

                            results.append(("attributes", "type_id", "enum", enum_id))

        return results


class MarkObservablesPlanner(Planner):
    def __init__(self, schema: ProtoSchema, options: CompilationOptions):
        super().__init__(schema, options)
        self._registry = _Registry(schema)

    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        ops: Analysis = []

        if self._options.set_observable is True and isinstance(input.data, DefnWithAttrs):
            ops.append(MarkObservablesOp(input.path, registry=self._registry))

        return ops


class BuildObservableTypesPlanner(Planner):
    def __init__(self, schema: ProtoSchema, options: CompilationOptions):
        super().__init__(schema, options)
        self._registry = _Registry(schema)

    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        ops: Analysis = []

        if input.path == SpecialFiles.DICTIONARY or (
            isinstance(input.data, ObjectDefn) or isinstance(input.data, EventDefn)
        ):
            ops.append(
                BuildObservableTypeOp(target=SpecialFiles.OBSERVABLE, prerequisite=input.path, registry=self._registry)
            )

        return ops
