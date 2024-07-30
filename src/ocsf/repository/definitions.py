"""A collection of data classes representing the metaschema of the OCSF."""

from abc import ABC
from dataclasses import dataclass
from typing import Any, Optional, TypeVar


IncludeTarget = str | list[str]


class DefinitionPart(ABC): ...


class DefinitionData(DefinitionPart): ...


@dataclass
class VersionDefn(DefinitionData):
    version: Optional[str] = None


@dataclass
class EnumMemberDefn(DefinitionPart):
    """An enum member. Enums are dictionaries of str: EnumMemberDefn."""

    caption: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class DeprecationInfoDefn(DefinitionPart):
    """Deprecation information for an object, event, or attribute."""

    message: Optional[str] = None
    since: Optional[str] = None


@dataclass
class TypeDefn(DefinitionPart):
    """A data type definition."""

    caption: Optional[str] = None
    description: Optional[str] = None
    is_array: Optional[bool] = None
    deprecated: Optional[DeprecationInfoDefn] = None
    max_len: Optional[int] = None
    observable: Optional[int] = None
    range: Optional[list[int]] = None
    regex: Optional[str] = None
    type: Optional[str] = None
    type_name: Optional[str] = None
    values: Optional[list[Any]] = None


@dataclass
class DictionaryTypesDefn(DefinitionPart):
    attributes: Optional[dict[str, TypeDefn | IncludeTarget]] = None
    caption: Optional[str] = None
    description: Optional[str] = None


@dataclass
class AttrDefn(DefinitionPart):
    """An attribute definition."""

    caption: Optional[str] = None
    requirement: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    is_array: Optional[bool] = None
    deprecated: Optional[DeprecationInfoDefn] = None
    enum: Optional[dict[str, EnumMemberDefn]] = None
    group: Optional[str] = None
    observable: Optional[int] = None
    profile: Optional[str | list[str]] = None
    sibling: Optional[str] = None
    object_type: Optional[str] = None
    object_name: Optional[str] = None


@dataclass
class DictionaryDefn(DefinitionData):
    """A dictionary definition."""

    name: Optional[str] = None
    caption: Optional[str] = None
    description: Optional[str] = None
    attributes: Optional[dict[str, AttrDefn | IncludeTarget]] = None
    types: Optional[DictionaryTypesDefn] = None


@dataclass
class ObjectDefn(DefinitionData):
    """An object definition."""

    caption: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    attributes: Optional[dict[str, AttrDefn | IncludeTarget]] = None
    extends: Optional[str] = None
    observable: Optional[int] = None
    profiles: Optional[list[str]] = None
    constraints: Optional[dict[str, list[str]]] = None
    deprecated: Optional[DeprecationInfoDefn] = None
    include_: Optional[IncludeTarget] = None
    src_extension: Optional[str] = None
    key: Optional[str] = None

    def get_key(self) -> Optional[str]:
        """Return the key for the object definition with the extension prefix when appropriate."""
        if self.key is None:
            return self.name
        else:
            return self.key


@dataclass
class EventDefn(DefinitionData):
    """An event definition."""

    caption: Optional[str] = None
    name: Optional[str] = None
    attributes: Optional[dict[str, AttrDefn | IncludeTarget]] = None
    description: Optional[str] = None
    uid: Optional[int] = None
    category: Optional[str] = None
    extends: Optional[str] = None
    profiles: Optional[list[str]] = None
    associations: Optional[dict[str, list[str]]] = None
    constraints: Optional[dict[str, list[str]]] = None
    deprecated: Optional[DeprecationInfoDefn] = None
    include_: Optional[IncludeTarget] = None
    src_extension: Optional[str] = None
    key: Optional[str] = None

    def get_key(self) -> Optional[str]:
        """Return the key for the object definition with the extension prefix when appropriate."""
        if self.key is None:
            return self.name
        else:
            return self.key


@dataclass
class IncludeDefn(DefinitionData):
    """An include definition."""

    caption: Optional[str] = None
    description: Optional[str] = None
    attributes: Optional[dict[str, AttrDefn | IncludeTarget]] = None
    annotations: Optional[AttrDefn] = None


@dataclass
class ProfileDefn(DefinitionData):
    """A profile definition."""

    caption: Optional[str] = None
    name: Optional[str] = None
    meta: Optional[str] = None
    description: Optional[str] = None
    attributes: Optional[dict[str, AttrDefn | IncludeTarget]] = None
    deprecated: Optional[DeprecationInfoDefn] = None
    annotations: Optional[AttrDefn] = None
    src_extension: Optional[str] = None
    key: Optional[str] = None

    def get_key(self) -> Optional[str]:
        """Return the key for the object definition with the extension prefix when appropriate."""
        if self.key is None:
            return self.name
        else:
            return self.key


@dataclass
class ExtensionDefn(DefinitionData):
    """An extension definition."""

    name: Optional[str] = None
    uid: Optional[int] = None
    caption: Optional[str] = None
    version: Optional[str] = None
    description: Optional[str] = None
    deprecated: Optional[DeprecationInfoDefn] = None


@dataclass
class CategoryDefn(DefinitionPart):
    """A category definition."""

    caption: Optional[str] = None
    description: Optional[str] = None
    uid: Optional[int] = None
    type: Optional[str] = None


@dataclass
class CategoriesDefn(DefinitionData):
    """A list of categories."""

    attributes: Optional[dict[str, CategoryDefn | IncludeTarget]] = None
    caption: Optional[str] = None
    description: Optional[str] = None
    name: Optional[str] = None


DefinitionT = TypeVar("DefinitionT", bound=DefinitionData, covariant=True)

AnyDefinition = (
    ObjectDefn | EventDefn | ProfileDefn | ExtensionDefn | DictionaryDefn | IncludeDefn | CategoriesDefn | VersionDefn
)

DefnWithName = ObjectDefn | EventDefn | ExtensionDefn | ProfileDefn
"""Definitions with a name property."""

DefnWithAttrs = ObjectDefn | EventDefn | ProfileDefn | DictionaryDefn | IncludeDefn
"""Definitions with attributes of type dict[str, AttrDefn]."""

DefnWithInclude = ObjectDefn | EventDefn
"""Definitions that support include directives at their root."""

DefnWithAnnotations = ProfileDefn | IncludeDefn
"""Definitions that support annotations."""

DefnWithExtn = ObjectDefn | EventDefn | ProfileDefn
"""Definitions that can be introduced to the core schema by an extension.

This is only used for definitions that create new record types in the core schema. `dictionary.json` is exempt.
"""
