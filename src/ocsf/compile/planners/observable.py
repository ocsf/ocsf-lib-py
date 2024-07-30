"""Assign the observable value to attributes in the compiled schema output based
on type and attribute name.

This will set the observable ID on all attributes with a type that has an
observable Type ID in the dictionary.json file or an attribute by the same name
with an observable ID in the dictionary.json file.

Producers and consumers wishing to build the observables attribute of records
can use this observable property to do so rather than implementing their own
logic to determine the correct observable type_id of attributes.
"""

from dataclasses import dataclass
from typing import Optional

from ..protoschema import ProtoSchema
from ..merge import MergeResult
from ..options import CompilationOptions

from .planner import Operation, Planner, Analysis
from ocsf.repository import (
    DefinitionFile,
    AttrDefn,
    TypeDefn,
    DefnWithAttrs,
    AnyDefinition,
    SpecialFiles,
    DictionaryDefn,
    DictionaryTypesDefn,
)


class _Registry:
    """A registry of observable attributes and types from the dictionary.json
    file so that the mapping can be computed once across all operations.
    """

    def __init__(self, schema: ProtoSchema):
        self._schema = schema
        self._types: Optional[dict[str, int]] = None
        self._attrs: Optional[dict[str, int]] = None

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


@dataclass(eq=True, frozen=True)
class MarkObservablesOp(Operation):
    registry: Optional[_Registry] = None

    def __str__(self):
        return f"Set observables in {self.target}"

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
                    if name in attrs:
                        attr.observable = attrs[name]
                        results.append(("attributes", name, "observable"))
                    elif attr.type in types:
                        attr.observable = types[attr.type]
                        results.append(("attributes", name, "observable"))

        return results


class MarkObservablesPlanner(Planner):
    def __init__(self, schema: ProtoSchema, options: CompilationOptions):
        super().__init__(schema, options)
        self._registry = _Registry(schema)

    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        if self._options.set_observable is False:
            return []

        if input.data is not None:
            if isinstance(input.data, DefnWithAttrs):
                return MarkObservablesOp(input.path, registry=self._registry)
