"""Simple formatted output of ChangedModels.

This modules prints a ChangedModel to stdout in a format similar to diff with
color coding.
"""

from typing import Any, cast

from textwrap import shorten
from termcolor import colored

from ocsf.schema import OcsfT
from .model import ChangedModel, Difference, SimpleDifference, Addition, Change, Removal


def _display(value: Any, line_length: int = 80) -> str:
    """Shorten the string representation of a value to fit within a certain width."""
    return shorten(str(value), width=line_length, placeholder="...")


def _format(value: SimpleDifference[Any], path: tuple[str, ...], collapse_changes: bool = True) -> None:
    """Format simple differences: Addition, Removal, and Change."""
    name = ".".join(path)

    if isinstance(value, Addition):
        print(colored(f"+ {name}: {_display(value.after)}", "green"))

    elif isinstance(value, Removal):
        print(colored(f"- {name}: {_display(value.before)}", "red"))

    elif isinstance(value, Change):
        if collapse_changes:
            print(colored(f"~ {name}: {_display(value.before, 35)} => {_display(value.after, 35)}", "cyan"))
        else:
            print(colored(f"+ {name}: {_display(value.after)}", "green"))
            print(colored(f"- {name}: {_display(value.before)}", "red"))

    else:
        raise ValueError(f"Unknown SimpleDifference type: {type(value)}")


def format(value: ChangedModel[OcsfT], path: tuple[str, ...] = (), collapse_changes: bool = True) -> None:
    """Format a ChangedModel recursively."""

    for attr_name in dir(value):
        # Ignore private and protected attributes
        if attr_name.startswith("_"):
            continue

        attr_val = getattr(value, attr_name)
        if isinstance(attr_val, SimpleDifference):
            # Addition, Removal, Change, and NoChange are handled here
            _format(cast(SimpleDifference[Any], attr_val), path + (attr_name,), collapse_changes)

        elif isinstance(attr_val, ChangedModel):
            # Recursively format nested ChangedModels
            format(attr_val, path + (attr_name,), collapse_changes)  # type:ignore

        elif isinstance(attr_val, dict):
            # Format nested dictionaries
            for key, v in cast(dict[str, Difference[Any]], attr_val).items():
                k = str(key)
                if isinstance(v, ChangedModel):
                    format(v, path + (attr_name, k), collapse_changes)
                elif isinstance(v, SimpleDifference):
                    _format(v, path + (attr_name, k), collapse_changes)

        else:
            # NoChange
            ...
