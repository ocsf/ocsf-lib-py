"""Models representing comparisons of OCSF schema elements.

This module provides a class hierarchy for representing differences between any
two data encountered in the OCSF schema, but especially between OCSF schema
models (events, objects, attributes, etc.).

```
                       Difference[T]
                           │
            ┌──────────────┴──────────────┬──────────────────────┐
            │                             │                      │
  SimpleDifference[T]               ChangedModel[T]           NoChange[T]
            │                             │
            │                             │
Addition[T]─┼─Removal[T]   ChangedObject──┼──ChangedSchema
            │                             │
            │                             │
        Change[T]            ChangedEvent─┴─ChangedAttr
```

At the top of the hierarchy is the abstract class Difference[T].

NoChange is a special case of Difference that represents the absence of any
difference. None is not used because T may be or contain NoneType.

The SimpleDifference[T] classes represent differences between any values.
Addition[T] and Removal[T] represent changes to a set or dictionary, while
Change[T] represents a change to a single value. These objects will contain a
before: T, after: T, or both as is appropriate.

The ChangedModel[T] classes represents a change to an OCSF model. Every model in
the schema package has a corresponding concrete ChangedModel class. These classes
contain fields for each attribute of the model, each of which is a
Difference[T].

Note that dictionaries get special treatment. Properties of OcsfModel that are
dictionaries will be represented as a dict[str, Difference]. When compared, the
dictionary will contain all keys from both operands. At each key will be the
Difference between values for that key. These may be Addition, Removal, Change,
NoChange, or a ChangedModel.

When modeling Optional dictionaries, be sure to use a type that is a Union of
the appropriate dict and NoChange. See ChangedAttr.enum for an example.

"""

from dataclasses import dataclass, field
from typing import Any, TypeVar, Generic, Optional
from abc import ABC

from ocsf.schema import (
    OcsfAttr,
    OcsfDeprecationInfo,
    OcsfEnumMember,
    OcsfEvent,
    OcsfExtension,
    OcsfObject,
    OcsfProfile,
    OcsfSchema,
    OcsfT,
    OcsfType,
    OcsfVersion,
)


T = TypeVar("T", covariant=True)


class Difference(ABC, Generic[T]): ...


class SimpleDifference(Difference[T]): ...


@dataclass
class Addition(SimpleDifference[T]):
    after: T


@dataclass
class Removal(SimpleDifference[T]):
    before: T


@dataclass
class Change(SimpleDifference[T]):
    before: Optional[T]
    after: Optional[T]


@dataclass
class NoChange(Difference[T]): ...


class ChangedModel(Difference[OcsfT]): ...


# class ChangedModel(ChangedModel[OcsfModel]): ...


@dataclass
class ChangedVersion(ChangedModel[OcsfVersion]):
    version: Difference[str] = field(default_factory=NoChange)


@dataclass
class ChangedEnumMember(ChangedModel[OcsfEnumMember]):
    caption: Difference[str] = field(default_factory=NoChange)
    description: Difference[Optional[str]] = field(default_factory=NoChange)
    notes: Difference[Optional[str]] = field(default_factory=NoChange)


@dataclass
class ChangedDeprecationInfo(ChangedModel[OcsfDeprecationInfo]):
    message: Difference[str] = field(default_factory=NoChange)
    since: Difference[str] = field(default_factory=NoChange)


@dataclass
class ChangedType(ChangedModel[OcsfType]):
    caption: Difference[str] = field(default_factory=NoChange)
    description: Difference[Optional[str]] = field(default_factory=NoChange)
    is_array: Difference[bool] = field(default_factory=NoChange)
    deprecated: Difference[Optional[ChangedDeprecationInfo]] = field(default_factory=NoChange)
    max_len: Difference[Optional[int]] = field(default_factory=NoChange)
    observable: Difference[Optional[int]] = field(default_factory=NoChange)
    range: Difference[Optional[list[int]]] = field(default_factory=NoChange)
    regex: Difference[Optional[str]] = field(default_factory=NoChange)
    type: Difference[Optional[str]] = field(default_factory=NoChange)
    type_name: Difference[Optional[str]] = field(default_factory=NoChange)
    values: Difference[Optional[list[Any]]] = field(default_factory=NoChange)


@dataclass
class ChangedAttr(ChangedModel[OcsfAttr]):
    caption: Difference[str] = field(default_factory=NoChange)
    description: Difference[Optional[str]] = field(default_factory=NoChange)
    requirement: Difference[str] = field(default_factory=NoChange)
    type: Difference[str] = field(default_factory=NoChange)
    is_array: Difference[bool] = field(default_factory=NoChange)
    enum: dict[str, Difference[OcsfEnumMember]] | NoChange[None] = field(default_factory=NoChange)
    group: Difference[Optional[str]] = field(default_factory=NoChange)
    observable: Difference[Optional[int]] = field(default_factory=NoChange)
    sibling: Difference[Optional[str]] = field(default_factory=NoChange)
    profile: Difference[Optional[str | list[str]]] = field(default_factory=NoChange)
    deprecated: Difference[Optional[OcsfDeprecationInfo]] = field(default_factory=NoChange)


@dataclass
class ChangedObject(ChangedModel[OcsfObject]):
    caption: Difference[str] = field(default_factory=NoChange)
    name: Difference[str] = field(default_factory=NoChange)
    attributes: dict[str, Difference[OcsfAttr]] = field(default_factory=dict)
    description: Difference[Optional[str]] = field(default_factory=NoChange)
    extends: Difference[Optional[str]] = field(default_factory=NoChange)
    observable: Difference[Optional[int]] = field(default_factory=NoChange)
    profiles: Difference[Optional[list[str]]] = field(default_factory=NoChange)
    constraints: dict[str, Difference[list[str]]] = field(default_factory=dict)
    deprecated: Difference[Optional[OcsfDeprecationInfo]] = field(default_factory=NoChange)


@dataclass
class ChangedEvent(ChangedModel[OcsfEvent]):
    caption: Difference[str] = field(default_factory=NoChange)
    name: Difference[str] = field(default_factory=NoChange)
    attributes: dict[str, Difference[OcsfAttr]] = field(default_factory=dict)
    description: Difference[Optional[str]] = field(default_factory=NoChange)
    uid: Difference[Optional[int]] = field(default_factory=NoChange)
    category: Difference[Optional[str]] = field(default_factory=NoChange)
    extends: Difference[Optional[str]] = field(default_factory=NoChange)
    profiles: Difference[Optional[list[str]]] = field(default_factory=NoChange)
    associations: dict[str, Difference[list[str]]] = field(default_factory=dict)
    constraints: dict[str, Difference[list[str]]] = field(default_factory=dict)
    include: Difference[Optional[str]] = field(default_factory=NoChange)
    deprecated: Difference[Optional[OcsfDeprecationInfo]] = field(default_factory=NoChange)


@dataclass
class ChangedProfile(ChangedModel[OcsfProfile]):
    caption: Difference[str] = field(default_factory=NoChange)
    name: Difference[str] = field(default_factory=NoChange)
    meta: Difference[str] = field(default_factory=NoChange)
    description: Difference[Optional[str]] = field(default_factory=NoChange)
    attributes: dict[str, Difference[OcsfAttr]] = field(default_factory=dict)
    deprecated: Difference[Optional[OcsfDeprecationInfo]] = field(default_factory=NoChange)
    annotations: dict[str, Difference[str]] = field(default_factory=dict)


@dataclass
class ChangedExtension(ChangedModel[OcsfExtension]):
    name: Difference[str] = field(default_factory=NoChange)
    version: Difference[Optional[str]] = field(default_factory=NoChange)
    uid: Difference[int] = field(default_factory=NoChange)
    caption: Difference[str] = field(default_factory=NoChange)
    description: Difference[Optional[str]] = field(default_factory=NoChange)
    deprecated: Difference[Optional[OcsfDeprecationInfo]] = field(default_factory=NoChange)


@dataclass
class ChangedSchema(ChangedModel[OcsfSchema]):
    classes: dict[str, Difference[OcsfEvent]] = field(default_factory=dict)
    objects: dict[str, Difference[OcsfObject]] = field(default_factory=dict)
    version: Difference[OcsfVersion] = field(default_factory=NoChange)
    types: dict[str, ChangedType] = field(default_factory=dict)
    base_event: Difference[Optional[OcsfEvent]] = field(default_factory=NoChange)
    profiles: dict[str, Difference[OcsfProfile]] = field(default_factory=dict)
    extensions: dict[str, Difference[OcsfExtension]] = field(default_factory=dict)
