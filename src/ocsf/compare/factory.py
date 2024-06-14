"""OCSF Comparison Factory

This module contains a factory function to create a specific ChangedModel instance to match a specific OCSF model.

Example:

    >>> from ocsf_schema.model import OcsfSchema
    >>> from ocsf_diff.factory import create_diff
    >>> schema = OcsfSchema(...)
    >>> diff = create_diff(schema)
    >>> print(diff) # ChangedSchema(...)

"""

from typing import cast

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
from .model import (
    ChangedAttr,
    ChangedDeprecationInfo,
    ChangedEnumMember,
    ChangedEvent,
    ChangedExtension,
    ChangedModel,
    ChangedObject,
    ChangedProfile,
    ChangedSchema,
    ChangedType,
    ChangedVersion,
)


def create_diff(model: OcsfT) -> ChangedModel[OcsfT]:
    """Factory to create a specific ChangedModel to match a given OCSF Model.

    The subclasses of ChangedModel are used to represent the differences between
    two instances of the corresponding OCSF model. There is a specific
    ChangeModel for every OCSF model type, like ChangedSchema for OcsfSchema,
    ChangedEvent for OcsfEvent, etc.

    Args:
        model: The OCSF model to create a diff for. Must be a subclass of OcsfModel, like OcsfAttr or OcsfEvent.

    Returns:
        A ChangedModel instance that corresponds to the given OCSF model.

    Raises:
        ValueError: If the given model is not a recognized OCSF model type.
    """

    match model:
        case OcsfSchema():
            ret = ChangedSchema()
        case OcsfEvent():
            ret = ChangedEvent()
        case OcsfObject():
            ret = ChangedObject()
        case OcsfAttr():
            ret = ChangedAttr()
        case OcsfDeprecationInfo():
            ret = ChangedDeprecationInfo()
        case OcsfVersion():
            ret = ChangedVersion()
        case OcsfEnumMember():
            ret = ChangedEnumMember()
        case OcsfExtension():
            ret = ChangedExtension()
        case OcsfProfile():
            ret = ChangedProfile()
        case OcsfType():
            ret = ChangedType()
        case _:
            raise ValueError("Unrecognized OCSF model type")

    # I have tried a lot of things – union types, @overloads, TypeGuards, etc. –
    # to avoid this cast while still satisfying the type checker in strict mode,
    # but all have failed.
    return cast(ChangedModel[OcsfT], ret)
