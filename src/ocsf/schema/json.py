"""Transform OCSF schema to and from JSON in strings and files.

Examples:
```python
schema = from_json('{"version": "1.0.0", "classes": [], "objects": []}')
schema = from_file("schema.json")
```

"""

import json
from dataclasses import asdict, dataclass
from typing import Any, cast

import dacite

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


def _unwrap_attributes(data: Any) -> dict[str, Any] | None:
    """If the given data is a dictionary with an "attributes" key whose value is also a dictionary, 
    return the value of the "attributes" key. Otherwise, return None."""
    if not isinstance(data, dict):
        return None

    entry = cast(dict[str, Any], data)
    attributes = entry.get("attributes")
    if not isinstance(attributes, dict):
        return None

    return cast(dict[str, Any], attributes)


def _with_name(name: str, data: Any) -> dict[str, Any]:
    """Add a name property to a dictionary if it is not already present."""
    if not isinstance(data, dict):
        raise ValueError(f"Invalid schema entry for {name}")

    entry = dict(cast(dict[str, Any], data))
    entry.setdefault("name", name)
    return entry


def normalize_schema_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize server payload differences before deserializing a schema."""
    # For v2 payloads, the data-type registry lives under dictionary.types.attributes.
    dictionary_entry = data.get("dictionary")
    dictionary = _unwrap_attributes(dictionary_entry)
    dictionary_types = None
    if isinstance(dictionary_entry, dict):
        dictionary_types = _unwrap_attributes(cast(dict[str, Any], dictionary_entry).get("types"))

    if dictionary_types is not None and "types" not in data:
        data["types"] = dictionary_types

    # If a categories dictionary is present, promote it to the top level and add names to each category entry.
    categories = _unwrap_attributes(data.get("categories"))
    if categories is not None:
        data["categories"] = {name: _with_name(name, value) for name, value in categories.items()}

    # If profiles are present but the top-level "profiles" key is missing, set profiles to null to avoid deserialization errors.
    profiles = data.get("profiles")
    if dictionary is not None and isinstance(profiles, dict):
        profile_map = cast(dict[str, Any], profiles)
        if all(isinstance(profile, dict) and "attributes" not in profile for profile in profile_map.values()):
            data["profiles"] = None

    return data


@dataclass
class SchemaOptions:
    """Options for hydrating OCSF schema properties."""

    resolve_object_types: bool = True
    """If true, replace object_t attribute types with the object type name as it
    appears in the attribute dictionary."""


def keys_to_names(d: dict[str, Any]) -> dict[str, Any]:
    """Transform OCSF property names in JSON to Python-friendly names."""
    xform: dict[str, Any] = {}

    for k, v in d.items():
        if k in _KEY_TRANSFORMS:
            k = _KEY_TRANSFORMS[k]

        if isinstance(v, dict):
            xform[k] = keys_to_names(cast(dict[str, Any], v))
        else:
            xform[k] = v

    return xform


def names_to_keys(d: dict[str, Any]) -> dict[str, Any]:
    """Transform Python-friendly names to OCSF property names in JSON."""
    xform: dict[str, Any] = {}

    for k, v in d.items():
        if k in _NAME_TRANSFORMS:
            k = _NAME_TRANSFORMS[k]

        if isinstance(v, dict):
            xform[k] = names_to_keys(cast(dict[str, Any], v))
        else:
            xform[k] = v

    return xform


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


def from_dict(data: dict[str, Any], options: SchemaOptions | None = None) -> OcsfSchema:
    """Parse an OCSF schema from a dictionary."""
    _options = SchemaOptions() if options is None else options
    normalized_data = normalize_schema_dict(data)

    schema = dacite.from_dict(OcsfSchema, keys_to_names(normalized_data))

    if _options.resolve_object_types:
        resolve_object_types(schema)

    return schema


def from_json(data: str, options: SchemaOptions | None = None) -> OcsfSchema:
    """Parse an OCSF schema from a JSON string."""
    _options = SchemaOptions() if options is None else options
    return from_dict(json.loads(data), _options)


def to_dict(schema: OcsfSchema) -> dict[str, Any]:
    """Convert an OCSF schema to a dictionary."""
    return names_to_keys(asdict(schema))


def to_json(schema: OcsfSchema) -> str:
    """Convert an OCSF schema to a JSON string."""
    return json.dumps(to_dict(schema))


def from_file(path: str, options: SchemaOptions | None = None) -> OcsfSchema:
    """Parse an OCSF schema from a JSON file."""
    with open(path) as f:
        return from_json(f.read())


def to_file(schema: OcsfSchema, path: str) -> None:
    """Write an OCSF schema to a JSON file."""
    with open(path, "w") as f:
        f.write(to_json(schema))
