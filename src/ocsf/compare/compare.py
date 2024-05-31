"""Compare OCSF schemata.

Herein are the functions for comparing two data of the same type.

compare() returns a Difference[T] object based on the comparison of the two
data. For primitives, the result will be a Change or a NoChange object. But for
OCSF models, the result will be a ChangedModel object with the differences of
the model's attributes.

compare_dict() is similar, but it works on dictionaries (or Optional[dict]). The
result is a dictionary will always have all of the keys from both dictionaries,
with the values being the differences of the corresponding keys.
"""

from typing import (
    TypeVar,
    TypeGuard,
    Union,
    get_args,
    get_type_hints,
    get_origin,
    Any,
    cast,
)
from types import UnionType, NoneType

from ocsf.schema import OcsfModel
from .model import (
    Difference,
    Addition,
    Removal,
    Change,
    NoChange,
)
from .factory import create_diff


T = TypeVar("T")
K = TypeVar("K")


def compare_dict(old_val: dict[K, T] | None, new_val: dict[K, T] | None) -> dict[K, Difference[T]] | NoChange[T]:
    """Compare two dictionaries and return the differences.

    If both arguments are None, the result will be a NoChange object.

    If either argument is a dictionary, the result will be a dictionary with all
    keys from both arguments. The values will be Difference objects.

    If a key is only present in one of the dictionaries, the result will be an
    Addition[T] or Removal[T].

    If a key is present in both dictionaries, the resulting value at the key
    will be a NoChange[T]. Otherwise, primitive values will result in a
    Change[T] and OcsfModel values will result in a ChangedModel[T].

    Args:
        old_val: The old dictionary to be compared. Must be a dictionary of the same type as new_val or None.
        new_val: The new dictionary to be compared. Must be a dictionary of the same type as old_val or None.

    Returns:
        A dictionary with all keys from both dictionaries and the differences of
        the values, or NoChange if both old_val and new_val are None.
    """

    if old_val is None and new_val is None:
        return NoChange()

    if old_val is None:
        old_val = {}

    if new_val is None:
        new_val = {}

    ret: dict[K, Difference[T]] = {}
    keys: set[K] = set(old_val.keys()) | set(new_val.keys())

    for key in keys:
        if key not in new_val:
            ret[key] = Removal(before=old_val[key])
        elif key not in old_val:
            ret[key] = Addition(after=new_val[key])
        elif old_val[key] == new_val[key]:
            ret[key] = NoChange()
        else:
            ret[key] = compare(old_val[key], new_val[key])

    return ret


def is_optional_dict(
    value: dict[Any, Any] | None, origin: type | UnionType, args: tuple[type, ...]
) -> TypeGuard[dict[Any, Any] | None]:
    """Check if a value is a dictionary or an Optional[dict].

    Args:
        value: The value to test.
        origin: The origin of the type hint (see: typing.get_origin).
        args: The arguments of the type hint (see: typing.get_args).
    """

    if isinstance(value, dict):
        return True

    if (origin != Union and origin != UnionType) or len(args) != 2:
        return False

    for arg in args:
        arg_origin = get_origin(arg)
        if arg is not NoneType and arg_origin is not dict:
            return False

    return True


def compare(old_val: T, new_val: T) -> Difference[T]:
    """Compare two values of the same type and return a Difference.

    If the values are primitives (int, bool, list[int], etc.), the result will
    always be a Change or a NoChange object.

    If the values are OcsfModel objects, the result will be a ChangedModel of
    the corresponding type (OcsfSchema -> ChangedSchema, etc.).

    The attributes of the resulting ChangedModel will all be Differences or, in
    the case of dictionaries, a dict[K, Difference[_]].

    Primitive attributes are represented with a Change or NoChange object.

    OcsfModel attributes are represented with a ChangedModel object (ChangedAttr,
    ChangedObject, etc.).

    Dictionary attributes are represented with a dict[K, Difference[_]] object.
    The combined keys of both dictionaries will be present in the result, and
    the values will be a Difference. See compare_dict for more details.

    Args:
        old_val: The old value to be compared.
        new_val: The new value to be compared.

    Returns:
        A suitable Difference object representing the comparison of the two values.
    """
    if isinstance(old_val, OcsfModel) and type(old_val) == type(new_val):
        ret = create_diff(old_val)

        for attr, value in get_type_hints(old_val).items():
            old_attr = getattr(old_val, attr)
            new_attr = getattr(new_val, attr)

            origin = get_origin(value)
            args = get_args(value)

            if is_optional_dict(old_attr, origin, args) and is_optional_dict(new_attr, origin, args):
                setattr(ret, attr, compare_dict(old_attr, new_attr))
            else:
                setattr(ret, attr, compare(old_attr, new_attr))

        return cast(Difference[T], ret)

    elif old_val == new_val:
        return NoChange()

    else:
        return Change(before=old_val, after=new_val)
