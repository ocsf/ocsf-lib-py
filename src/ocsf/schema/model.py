"""This module contains the dataclasses that represent the OCSF schema."""

from abc import ABC
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional, TypeVar


class OcsfModel(ABC): ...


# TODO: is this used?
@dataclass
class OcsfVersion(OcsfModel):
    version: str


@dataclass
class OcsfEnumMember(OcsfModel):
    """An enum member. Enums are dictionaries of str: OcsfEnumMember."""

    caption: str
    description: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class OcsfDeprecationInfo(OcsfModel):
    """Deprecation information for an object, event, or attribute."""

    message: str
    since: str


@dataclass
class OcsfType(OcsfModel):
    """A data type definition."""

    caption: str
    description: Optional[str] = None
    is_array: bool = False
    deprecated: Optional[OcsfDeprecationInfo] = None
    max_len: Optional[int] = None
    observable: Optional[int] = None
    range: Optional[list[int]] = None
    regex: Optional[str] = None
    type: Optional[str] = None
    type_name: Optional[str] = None
    values: Optional[list[Any]] = None


@dataclass
class OcsfAttr(OcsfModel):
    """An attribute definition."""

    caption: str
    requirement: str
    type: str
    description: Optional[str] = None
    is_array: bool = False
    deprecated: Optional[OcsfDeprecationInfo] = None
    enum: Optional[dict[str, OcsfEnumMember]] = None
    group: Optional[str] = None
    observable: Optional[int] = None
    profile: Optional[str | list[str]] = None
    sibling: Optional[str] = None


@dataclass
class OcsfObject(OcsfModel):
    """An object definition."""

    caption: str
    name: str
    description: Optional[str] = None
    attributes: dict[str, OcsfAttr] = field(default_factory=dict)
    extends: Optional[str] = None
    observable: Optional[int] = None
    profiles: Optional[list[str]] = None
    constraints: Optional[dict[str, list[str]]] = None
    deprecated: Optional[OcsfDeprecationInfo] = None


@dataclass
class OcsfEvent(OcsfModel):
    """An event definition."""

    caption: str
    name: str
    attributes: dict[str, OcsfAttr] = field(default_factory=dict)
    description: Optional[str] = None
    uid: Optional[int] = None
    category: Optional[str] = None
    extends: Optional[str] = None
    profiles: Optional[list[str]] = None
    associations: Optional[dict[str, list[str]]] = None
    constraints: Optional[dict[str, list[str]]] = None
    deprecated: Optional[OcsfDeprecationInfo] = None


@dataclass
class OcsfSchema(OcsfModel):
    """An OCSF schema as represented in the OCSF server's export endpoint."""

    version: str
    classes: dict[str, OcsfEvent] = field(default_factory=dict)
    objects: dict[str, OcsfObject] = field(default_factory=dict)
    types: dict[str, OcsfType] = field(default_factory=dict)
    base_event: Optional[OcsfEvent] = None


# A type variable constrained to OCSF models.
OcsfT = TypeVar("OcsfT", bound=OcsfModel, covariant=True)


class OcsfElementType(StrEnum):
    EVENT = "event"
    OBJECT = "object"
    ENUM_MEMBER = "enum"
    ATTRIBUTE = "attribute"
    TYPE = "type"
