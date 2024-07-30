import os
from typing import Optional
from ocsf.api import OcsfApiClient
from ocsf.schema import OcsfSchema, from_file
from ocsf.repository import read_repo
from ocsf.compile import Compilation, CompilationOptions


def get_schema(
    versionOrFile: Optional[str] = None,
    client: Optional[OcsfApiClient] = None,
    compile_options: CompilationOptions = CompilationOptions(),
) -> OcsfSchema:
    """Fetch a schema from a filename or version.

    This is a convenience function.

    Example:
        ```python
        schema = get_schema("1.1.0")
        schema = get_schema("ocsf-1.1.0.json")
        ```

    Args:
        versionOrFile: The name of an OCSF schema file or a valid semantic version number.

    Returns:
        The requested OcsfSchema.

    Raises:
        ValueError: If the version requested is not found on the server or
            if the requested version is invalid.
    """
    if versionOrFile is not None:
        if os.path.isdir(versionOrFile):
            repo = read_repo(versionOrFile)
            compilation = Compilation(repo, options=compile_options)
            return compilation.build()

        elif os.path.isfile(versionOrFile):
            return from_file(versionOrFile)

    if client is None:
        client = OcsfApiClient()

    return client.get_schema(versionOrFile)
