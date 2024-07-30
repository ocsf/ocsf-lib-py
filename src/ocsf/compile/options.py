from dataclasses import dataclass
from typing import Optional


@dataclass
class CompilationOptions:
    profiles: Optional[list[str]] = None
    """A list of profiles to enable while compiling. Defaults to all profiles."""

    extensions: Optional[list[str]] = None
    """A list of extension directories to compile. Defaults to extensions/*."""

    ignore_profiles: Optional[list[str]] = None
    """A list of profiles to ignore while compiling. Defaults to None."""

    ignore_extensions: Optional[list[str]] = None
    """A list of extension directories to ignore while compiling. Defaults to None."""

    prefix_extensions: bool = True
    """If True, prefix object and event names and any attributes that reference
    them as their type with the extension name.
    """

    set_object_types: bool = True
    """If True, set type to 'object' and object_type to the object name for type
    references to objects, as per the original OCSF server. If False, the type 
    field will refer directly to the object type.
    """
