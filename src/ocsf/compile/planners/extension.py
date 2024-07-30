from copy import deepcopy
from dataclasses import dataclass
from typing import Optional

from ..protoschema import ProtoSchema
from ..options import CompilationOptions
from ..merge import merge, MergeResult
from .planner import Operation, Planner, Analysis
from ocsf.repository import (
    DefinitionFile,
    extension,
    extensionless,
    AnyDefinition,
    as_path,
    DefnWithExtn,
    RepoPaths,
    SpecialFiles,
    ExtensionDefn,
    DefnWithAttrs,
    AttrDefn,
)


class ExtensionPlanner(Planner):
    def __init__(self, schema: ProtoSchema, options: CompilationOptions):
        if options.extensions is None:
            options.extensions = list(schema.repo.extensions())

        if options.ignore_extensions is not None:
            options.extensions = [ext for ext in options.extensions if ext not in options.ignore_extensions]

        super().__init__(schema, options)


@dataclass(eq=True, frozen=True)
class ExtensionModifyOp(Operation):
    def apply(self, schema: ProtoSchema) -> MergeResult:
        assert self.prerequisite is not None

        effected = schema[self.target]
        assert effected.data is not None

        source = schema[self.prerequisite]
        assert source.data is not None

        return merge(effected.data, source.data)

    def __str__(self):
        return f"Extension modifies {self.target} <- {self.prerequisite}"


class ExtensionMergePlanner(ExtensionPlanner):
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        # We forcibly initialize this in __init__; this assertion is for the
        # type checker's benefit.
        assert self._options.extensions is not None

        extn = extension(input.path)

        if extn is not None and extn in self._options.extensions:
            dest = extensionless(input.path)
            if dest in self._schema.repo:
                return ExtensionModifyOp(dest, input.path)

        return None


@dataclass(eq=True, frozen=True)
class ExtensionCopyOp(Operation):
    def apply(self, schema: ProtoSchema) -> MergeResult:
        assert self.prerequisite is not None

        source = schema[self.prerequisite]
        assert source.data is not None

        if not isinstance(source.data, DefnWithExtn):
            return []

        schema[self.target] = deepcopy(source)
        dest = schema[self.target]
        dest.path = self.target
        assert dest.data is not None

        # Here we merge just so that we have a MergeResult. This is slightly
        # inefficient but effective.
        return merge(dest.data, source.data, overwrite=True)

    def __str__(self):
        return f"Extension creates {self.target} <- {self.prerequisite}"


class ExtensionCopyPlanner(ExtensionPlanner):
    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        # We forcibly initialize this in __init__; this assertion is for the
        # type checker's benefit.
        assert self._options.extensions is not None

        extn = extension(input.path)

        if extn is not None and extn in self._options.extensions:
            dest = extensionless(input.path)
            if dest not in self._schema.repo:
                return ExtensionCopyOp(dest, input.path)

        return None


@dataclass(eq=True, frozen=True)
class MarkExtensionOp(Operation):
    def apply(self, schema: ProtoSchema) -> MergeResult:
        assert self.prerequisite is not None

        source = schema[self.prerequisite]
        assert source.data is not None

        if not isinstance(source.data, DefnWithExtn):
            return []

        # Look up the source extension name from extension.json (because it may not match the directory)
        extn_dir = extension(self.prerequisite)
        assert extn_dir is not None
        extn = schema[as_path(RepoPaths.EXTENSIONS, extn_dir, SpecialFiles.EXTENSION)]
        assert isinstance(extn.data, ExtensionDefn)
        assert extn.data.name is not None
        source.data.src_extension = extn.data.name

        return [("src_extension",)]

    def __str__(self):
        return f"Extension creates {self.target} <- {self.prerequisite}"


class MarkExtensionPlanner(ExtensionPlanner):
    """Set the src_extension property of an event or object to the name of the
    extension that introduced it to the schema.
    """

    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        assert self._options.extensions is not None

        extn = extension(input.path)

        if extn is not None and extn in self._options.extensions:
            dest = extensionless(input.path)
            if dest not in self._schema.repo:
                return MarkExtensionOp(dest, input.path)

        return None


@dataclass(eq=True, frozen=True)
class PrefixKeyOp(Operation):
    """Prefix the key of an object or event (where it is found in the schema) with its extension name."""

    # Prerequisite: MarkExtensionOp has been applied
    def apply(self, schema: ProtoSchema) -> MergeResult:
        source = schema[self.target]
        assert source.data is not None

        if not isinstance(source.data, DefnWithExtn):
            return []

        if source.data.src_extension is not None:
            assert source.data.name is not None
            source.data.key = "/".join((source.data.src_extension, source.data.name))
            return [("name",)]

        return []

    def __str__(self):
        return f"Prepend extension name to {self.target}"


class _ExtensionTypeMap:
    """This class builds a map of object and event type names to their prefixed
    names, so that this expensive(ish) operation can be O(1) instead of O(n).
    """

    def __init__(self, schema: ProtoSchema, extensions: list[str]):
        self._map: dict[str, str] = {}
        self._built: bool = False
        self._schema = schema
        self._extensions = extensions

    def _build(self):
        if self._built is True:
            return

        for path in self._schema.repo.paths():
            file = self._schema[path]
            extn = extension(file.path)
            if extn is not None and extn in self._extensions:
                if (isinstance(file.data, DefnWithExtn)) and file.data.src_extension is not None:
                    if file.data.key is not None and "/" in file.data.key:
                        new = file.data.key
                        old = file.data.key.split("/")[1]
                        self._map[old] = new

                    elif file.data.name is not None:
                        old = file.data.name
                        new = "/".join((file.data.src_extension, file.data.name))
                        self._map[old] = new

        self._built = True

    def __getitem__(self, key: str) -> str:
        self._build()
        return self._map[key]

    def __setitem__(self, key: str, value: str):
        self._map[key] = value

    def __contains__(self, key: str) -> bool:
        self._build()
        return key in self._map

    def __iter__(self):
        self._build()
        return iter(self._map)

    def __len__(self):
        self._build()
        return len(self._map)

    def __repr__(self):
        return repr(self._map)


@dataclass(eq=True, frozen=True)
class PrefixTypeOp(Operation):
    """This operation prefixes the type references of attributes with an extension name where appropriate."""

    map: Optional[_ExtensionTypeMap] = None

    def apply(self, schema: ProtoSchema) -> MergeResult:
        source = schema[self.target]
        assert source.data is not None

        if not isinstance(source.data, DefnWithAttrs):
            return []

        if self.map is None:
            raise Exception("PrefixTypeOp requires a map")

        results: MergeResult = []
        if source.data.attributes is not None:
            for name, attr in source.data.attributes.items():
                if isinstance(attr, AttrDefn) and attr.type is not None and attr.type in self.map:
                    attr.type = self.map[attr.type]
                    results.append(("attributes", name, "type"))

        return results


class ExtensionPrefixPlanner(ExtensionPlanner):
    def __init__(self, schema: ProtoSchema, options: CompilationOptions):
        super().__init__(schema, options)
        assert options.extensions is not None
        self._map = _ExtensionTypeMap(schema, options.extensions)

    def analyze(self, input: DefinitionFile[AnyDefinition]) -> Analysis:
        if self._options.prefix_extensions is False:
            return None

        assert self._options.extensions is not None

        ops: list[Operation] = []

        extn = extension(input.path)
        if extn is not None and extn in self._options.extensions:
            ops.append(PrefixKeyOp(input.path))

        if isinstance(input.data, DefnWithAttrs):
            ops.append(PrefixTypeOp(input.path, map=self._map))

        return ops
