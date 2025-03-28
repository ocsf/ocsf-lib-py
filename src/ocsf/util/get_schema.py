import os
from typing import Optional

from ocsf.api import OcsfApiClient
from ocsf.compile import Compilation, CompilationOptions
from ocsf.repository import read_repo
from ocsf.schema import OcsfSchema, from_file


def get_schema(
    version_or_file: Optional[str] = None,
    client: Optional[OcsfApiClient] = None,
    compile_options: CompilationOptions | None = None,
) -> OcsfSchema:
    """Fetch a schema from a filename or version.

    This is a convenience function.

    Example:
        ```python
        schema = get_schema("1.1.0")
        schema = get_schema("ocsf-1.1.0.json")
        ```

    Args:
        version_or_file: The name of an OCSF schema file or a valid semantic version number.

    Returns:
        The requested OcsfSchema.

    Raises:
        ValueError: If the version requested is not found on the server or
            if the requested version is invalid.
    """
    _compile_options = CompilationOptions() if compile_options is None else compile_options
    if version_or_file is not None:
        if os.path.isdir(version_or_file):
            repo = read_repo(version_or_file)
            compilation = Compilation(repo, options=_compile_options)
            return compilation.build()

        elif os.path.isfile(version_or_file):
            return from_file(version_or_file)

    if client is None:
        client = OcsfApiClient()

    return client.get_schema(version_or_file)
