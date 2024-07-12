"""Transform OCSF schema to and from JSON in strings and files.

Examples:
```python
schema = from_json('{"version": "1.0.0", "classes": [], "objects": []}')
schema = from_file("schema.json")
```

"""

import json
import dacite

from dataclasses import asdict, dataclass
from typing import Any, cast

from .model import OcsfSchema, WithAttributes

# Certain OCSF properties have special characters in their names.
_KEY_TRANSFORMS = {
    "@deprecated": "deprecated",
    "$include": "include_",
}

_NAME_TRANSFORMS = {
    "deprecated": "@deprecated",
    "include_": "$include",
}


@dataclass
class SchemaOptions:
    """Options for hydrating OCSF schema properties."""

    resolve_object_types: bool = True
    """If true, replace object_t attribute types with the object type name as it
    appears in the attribute dictionary."""


def keys_to_names(d: dict[str, Any]) -> dict[str, Any]:
    """Transform OCSF property names in JSON to Python-friendly names."""
    ops: list[tuple[str, str]] = []

    for k, v in d.items():
        if k in _KEY_TRANSFORMS:
            ops.append((k, _KEY_TRANSFORMS[k]))

        if isinstance(v, dict):
            d[k] = keys_to_names(cast(dict[str, Any], v))

    for op in ops:
        d[op[1]] = d[op[0]]
        del d[op[0]]

    return d


def names_to_keys(d: dict[str, Any]) -> dict[str, Any]:
    """Transform Python-friendly names to OCSF property names in JSON."""
    for k, v in d.items():
        if k in _NAME_TRANSFORMS:
            d[_NAME_TRANSFORMS[k]] = d[k]
            del d[k]

        if isinstance(k, dict):
            d[k] = names_to_keys(v)

    return d


def resolve_object_types(things: dict[str, WithAttributes] | OcsfSchema | WithAttributes) -> None:
    if isinstance(things, WithAttributes):
        for attr in things.attributes.values():
            if attr.type == "object_t" and attr.object_type is not None:
                attr.type = attr.object_type
        return

    if isinstance(things, OcsfSchema):
        items = list(things.classes.values()) + list(things.objects.values())

        if things.profiles is not None:
            items += list(things.profiles.values())
    else:
        items = list(things.values())

    for thing in items:
        resolve_object_types(thing)


def from_dict(data: dict[str, Any], options: SchemaOptions = SchemaOptions()) -> OcsfSchema:
    """Parse an OCSF schema from a dictionary."""
    schema = dacite.from_dict(OcsfSchema, keys_to_names(data))

    if options.resolve_object_types:
        resolve_object_types(schema)

    return schema


def from_json(data: str, options: SchemaOptions = SchemaOptions()) -> OcsfSchema:
    """Parse an OCSF schema from a JSON string."""
    return from_dict(json.loads(data), options)


def to_dict(schema: OcsfSchema) -> dict[str, Any]:
    """Convert an OCSF schema to a dictionary."""
    return names_to_keys(asdict(schema))


def to_json(schema: OcsfSchema) -> str:
    """Convert an OCSF schema to a JSON string."""
    return json.dumps(to_dict(schema))


def from_file(path: str, options: SchemaOptions = SchemaOptions()) -> OcsfSchema:
    """Parse an OCSF schema from a JSON file."""
    with open(path, "r") as f:
        return from_json(f.read())


def to_file(schema: OcsfSchema, path: str) -> None:
    """Write an OCSF schema to a JSON file."""
    with open(path, "w") as f:
        f.write(to_json(schema))
