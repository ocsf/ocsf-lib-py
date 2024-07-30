from copy import deepcopy
from dataclasses import dataclass
from typing import get_type_hints, cast, Optional, Any

from ocsf.repository.definitions import DefinitionPart

FieldList = list[str | tuple[str, ...]]


@dataclass
class MergeOptions:
    overwrite: Optional[bool] = None
    """Always overwrite left with right"""

    allowed_fields: Optional[FieldList] = None
    """Only update fields that are in this list or are nested under a field in this list"""

    ignored_fields: Optional[FieldList] = None
    """Ignore fields that are in this list or are nested under a field in this list"""

    add_dict_items: bool = True
    """Add missing dictionary items from right to left if True"""

    copy: bool = True
    """If True, always merge a copy of the right value rather than a reference"""

    overwrite_none: bool = False
    """If True, overwrite left with right even if right is None"""

    merge_lists: bool = True
    """If True, merge lists by combining their unique elements"""


def _can_update(path: tuple[str, ...], left_value: Any, right_value: Any, options: MergeOptions) -> bool:
    """Helper function to decide if a value should be updated.

    Below are truth tables showing the logic of this function.

    1. Default behavior
     - overwrite is False
     - allowed_fields is None or field is in allowed_fields
     - ignored_fields is None or field is not in ignored_fields
    |    | R0 | R1 |
    | L0 | 0  | 1  |
    | L1 | 0  | 0  |

    2. Overwrite behavior
     - overwrite is True
     - allowed_fields is None or field is in allowed_fields
     - ignored_fields is None or field is not in ignored_fields
    |    | R0 | R1 |
    | L0 | 1  | 1  |
    | L1 | 1  | 1  |

    3. Field is ignored or disallowed
     - overwrite is True or False
     - allowed_fields is not None and field is not in allowed_fields
     - ignored_fields is not None and field is in ignored_fields
    |    | R0 | R1 |
    | L0 | 0  | 0  |
    | L1 | 0  | 0  |

    Key:
        L0 = Left value is None
        L1 = Left value is not None
        R0 = Right value is None
        R1 = Right value is not None

    Args:

    """

    update: Optional[bool] = None

    def change_field():
        # If overwrite is True, we'll always update the left value.
        if options.overwrite and options.overwrite_none:
            return True

        elif options.overwrite and not options.overwrite_none and right_value is not None:
            return True

        elif options.merge_lists and isinstance(left_value, list) and isinstance(right_value, list):
            return True

        # Otherwise, we'll only update the left value if it's None.
        else:
            return left_value is None and right_value is not None

    # Narrow the update to specific white-listed fields if
    # allowed_fields is set.
    if options.allowed_fields is not None:
        update = False

        for allow in options.allowed_fields:
            if isinstance(allow, tuple):
                if path[: len(allow)] == allow:
                    update = change_field()
            else:
                if path[0] == allow:
                    update = change_field()

            if update:
                break

    # Skip black-listed fields if ignored_fields is set.
    elif options.ignored_fields is not None:
        for deny in options.ignored_fields:
            if isinstance(deny, tuple):
                if path[: len(deny)] == deny:
                    update = False
                    break
            else:
                if path[0] == deny:
                    update = False
                    break

    if update is None:
        update = change_field()

    return update


MergeResult = list[tuple[str, ...]]


def merge(
    left: DefinitionPart,
    right: DefinitionPart,
    overwrite: Optional[bool] = None,
    *,
    allowed_fields: Optional[FieldList] = None,
    ignored_fields: Optional[FieldList] = None,
    options: Optional[MergeOptions] = None,
    trail: tuple[str, ...] = tuple(),
) -> MergeResult:
    """Merge the right definition into the left definition."""

    # This will be a list of all paths of properties that were updated.
    results: MergeResult = []

    if options is None:
        options = MergeOptions()

    # Convert named parameters to options object
    if overwrite is not None:
        options.overwrite = overwrite
    if allowed_fields is not None:
        options.allowed_fields = allowed_fields
    if ignored_fields is not None:
        options.ignored_fields = ignored_fields

    # Now for the money: iterate over all attributes in the left definition and
    # update where necessary.
    for attr, _ in get_type_hints(left).items():
        # If the attribute isn't in the right operand, there's nothing to do.
        if hasattr(right, attr):
            path = trail + (attr,)

            left_value = getattr(left, attr)
            right_value = getattr(right, attr)
            if options.copy:
                right_value = deepcopy(right_value)
            simple = True

            # Recursively merge dictionaries
            ################################
            #
            if isinstance(left_value, dict) and isinstance(right_value, dict):
                left_value = cast(dict[Any, Any], left_value)
                right_value = cast(dict[Any, Any], right_value)

                if len(right_value) > 0:
                    simple = False

                    for key, value in right_value.items():
                        next_path = path + (key,)
                        if key not in left_value:
                            if options.add_dict_items and _can_update(next_path, None, value, options):
                                left_value[key] = value
                                results.append(next_path)
                        elif isinstance(left_value[key], DefinitionPart) and isinstance(value, DefinitionPart):
                            results += merge(left_value[key], value, options=options, trail=next_path)
                        # elif isinstance(left_value[key], list) and isinstance(value, list):
                        #    left_value[key] = list(set(left_value[key] + value))
                        #    results.append(next_path)
                        elif _can_update(path, left_value[key], right_value[key], options):
                            left_value[key] = value
                            results.append(next_path)

            # Merge lists
            #############
            # If both values are lists and the merge_lists option is set, we'll
            # combine list elements as if they were two sets.
            #
            elif (
                _can_update(path, left_value, right_value, options)
                and isinstance(left_value, list)
                and isinstance(right_value, list)
                and options.merge_lists
            ):
                simple = False
                # TODO check to see if these can be cast to list[str] - are there any other types of lists in the JSON definitions?
                left_value = cast(list[Any], left_value)
                right_value = cast(list[Any], right_value)
                setattr(left, attr, list(set(left_value + right_value)))
                results.append(path)

            # Merge DefinitionPart objects (OCSF complex types)
            ###################################################
            # If both values are DefinitionPart objects, we'll recursively merge
            # them using the same options this was invoked with.
            #
            elif isinstance(left_value, DefinitionPart) and isinstance(right_value, DefinitionPart):
                simple = False
                results += merge(left_value, right_value, options=options, trail=path)

            # Merge everything else
            #######################
            # For scalar values, lists, non-DefinitionPart dictionaries and
            # objects (OCSF complex types), or cases where one side is a
            # DefinitionPart and the other is None, merge the values according
            # to the options.
            #
            if simple and _can_update(path, left_value, right_value, options):
                setattr(left, attr, right_value)
                results.append(path)

    return results
