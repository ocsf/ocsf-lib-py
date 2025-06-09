"""This module contains the dataclasses that represent the OCSF schema."""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Optional, TypeVar


class OcsfModel: ...


# TODO: is this used?
@dataclass
class OcsfVersion(OcsfModel):
    version: str


@dataclass(slots=True)
class OcsfEnumMember(OcsfModel):
    """An enum member. Enums are dictionaries of str: OcsfEnumMember."""

    caption: str
    description: Optional[str] = None
    notes: Optional[str] = None


@dataclass(slots=True)
class OcsfDeprecationInfo(OcsfModel):
    """Deprecation information for an object, event, or attribute."""

    message: str
    since: str


@dataclass(slots=True)
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


@dataclass(slots=True)
class OcsfAttr(OcsfModel):
    """An attribute definition."""

    caption: str
    type: str
    requirement: str = "optional"
    description: Optional[str] = None
    is_array: bool = False
    deprecated: Optional[OcsfDeprecationInfo] = None
    enum: Optional[dict[str, OcsfEnumMember]] = None
    group: Optional[str] = None
    observable: Optional[int] = None
    profile: Optional[str | list[str]] = None
    sibling: Optional[str] = None
    object_type: Optional[str] = None
    object_name: Optional[str] = None
    type_name: Optional[str] = None

    def is_object(self) -> bool:
        return self.type[-2:] != "_t"

    def is_primitive(self) -> bool:
        return not self.is_object()


@dataclass(slots=True)
class OcsfObject(OcsfModel):
    """An object definition."""

    caption: str
    name: str
    description: Optional[str] = None
    attributes: dict[str, OcsfAttr] = field(default_factory=lambda: dict())
    extends: Optional[str] = None
    observable: Optional[int] = None
    profiles: Optional[list[str]] = None
    constraints: Optional[dict[str, list[str]]] = None
    deprecated: Optional[OcsfDeprecationInfo] = None


@dataclass(slots=True)
class OcsfEvent(OcsfModel):
    """An event definition."""

    caption: str
    name: str
    attributes: dict[str, OcsfAttr] = field(default_factory=lambda: dict())
    description: Optional[str] = None
    uid: Optional[int] = None
    category: Optional[str] = None
    extends: Optional[str] = None
    profiles: Optional[list[str]] = None
    associations: Optional[dict[str, list[str]]] = None
    constraints: Optional[dict[str, list[str]]] = None
    deprecated: Optional[OcsfDeprecationInfo] = None


@dataclass
class OcsfProfile(OcsfModel):
    """A profile definition."""

    caption: str
    name: str
    meta: str = "profile"
    description: Optional[str] = None
    attributes: dict[str, OcsfAttr] = field(default_factory=lambda: dict())
    deprecated: Optional[OcsfDeprecationInfo] = None
    annotations: Optional[dict[str, str]] = None


@dataclass
class OcsfExtension(OcsfModel):
    """An extension definition."""

    name: str
    uid: int
    caption: str
    version: Optional[str] = None
    description: Optional[str] = None
    deprecated: Optional[OcsfDeprecationInfo] = None


@dataclass(slots=True)
class OcsfCategory(OcsfModel):
    """A category definition."""

    name: str
    uid: int
    caption: str
    description: Optional[str] = None
    deprecated: Optional[OcsfDeprecationInfo] = None
    classes: Optional[dict[str, OcsfEvent]] = None


@dataclass(slots=True)
class OcsfSchema(OcsfModel):
    """An OCSF schema as represented in the OCSF server's export endpoint."""

    version: str
    classes: dict[str, OcsfEvent] = field(default_factory=lambda: dict())
    objects: dict[str, OcsfObject] = field(default_factory=lambda: dict())
    types: dict[str, OcsfType] = field(default_factory=lambda: dict())
    base_event: Optional[OcsfEvent] = None
    profiles: Optional[dict[str, OcsfProfile]] = None
    extensions: Optional[dict[str, OcsfExtension]] = None
    categories: Optional[dict[str, OcsfCategory]] = None


# A type variable constrained to OCSF models.
OcsfT = TypeVar("OcsfT", bound=OcsfModel, covariant=True)
WithAttributes = OcsfEvent | OcsfObject | OcsfProfile


class OcsfElementType(StrEnum):
    EVENT = "event"
    OBJECT = "object"
    ENUM_MEMBER = "enum"
    ATTRIBUTE = "attribute"
    TYPE = "type"
