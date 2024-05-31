"""
A simple caching HTTP client for fetching OCSF schemas from the server.

Example:

```python
from ocsf_tools.schema.http import OcsfServerClient
schema = OcsfServerClient().get_schema()
schema = OcsfServerClient(cache_dir="./schema_cache").get_schema("1.1.0")
```

TODO:
- This client is synchronous and only covers a small subset of the OCSF server's
  API. This could be replaced with a more robust OpenAPI client.
"""

import logging
import json

from dataclasses import dataclass
from urllib.request import urlopen
from urllib.parse import urljoin
from typing import Optional
from semver import Version
from pathlib import Path

from dacite import from_dict

from ocsf.schema import OcsfSchema, from_json, from_file, to_file


LOG = logging.getLogger(__name__)


def _is_semver(version: str) -> bool:
    """Is a version string a valid semantic version?"""
    try:
        Version.parse(version)
        return True
    except ValueError:
        return False


# Models representing the response from the OCSF server's /api/versions endpoint.
@dataclass
class SchemaVersion:
    url: str
    version: str


@dataclass
class SchemaVersions:
    default: SchemaVersion
    versions: list[SchemaVersion]


class OcsfApiClient:
    """A simple caching OCSF server client.

    This client uses a local filesystem cache to store schemas and avoid
    repeating requests to the OCSF server.
    """

    def __init__(self, base_url: str = "https://schema.ocsf.io", cache_dir: Optional[str | Path] = None):
        """Create a new client.

        Args:
            base_url: The base URL of the OCSF server.
            cache_dir: The directory to store cached schemas in.
        """
        self._base_url = base_url
        self._versions: Optional[SchemaVersions] = None
        if cache_dir is not None and not isinstance(cache_dir, Path):
            self._cache_dir = Path(cache_dir)
        else:
            self._cache_dir = cache_dir

    def _fetch_schema(self, version: Optional[str] = None) -> OcsfSchema:
        """Fetch a schema from the server."""
        if version is not None:
            url = urljoin(self._base_url, f"{version}/")
        else:
            url = self._base_url

        url = urljoin(url, "export/schema")

        LOG.debug(f"Fetching schema from {url} (version {version})")
        json_str = urlopen(url).read()
        return from_json(json_str)

    def _fetch_versions(self) -> SchemaVersions:
        """Fetch the available versions from the server."""
        url = urljoin(self._base_url, "api/versions")
        data = json.loads(urlopen(url).read())
        return from_dict(SchemaVersions, data)

    def get_versions(self) -> list[str]:
        """Return the available schema versions on the server."""
        if self._versions is None:
            self._versions = self._fetch_versions()

        return [v.version for v in self._versions.versions]

    def get_default_version(self) -> str:
        """Return the server's default schema version."""
        if self._versions is None:
            self._versions = self._fetch_versions()

        return self._versions.default.version

    def get_schema(self, version: Optional[str] = None) -> OcsfSchema:
        """Get a schema from the cache or from the server.

        If version is None, the server's default version is used. The cache will
        not be read, but it will be updated.

        If cache_dir is not set, no caching will be used.

        Example:
            ```python
            schema = OcsfServerClient().get_schema("1.1.0")
            ```

        Args:
            version: The version of the schema to fetch. If None, the server's
                default version is used.

        Returns:
            The requested OcsfSchema.

        Raises:
            ValueError: If the version requested is not found on the server or
                if the requested version is invalid.
        """
        if version is not None:
            # Ensure version is a valid semantic version string.
            if not _is_semver(version):
                raise ValueError(f"Invalid version: {version}")

            # Check the cache first.
            if self._cache_dir is not None:
                if not self._cache_dir.exists():
                    LOG.debug(f"Creating cache directory: {self._cache_dir}")
                    self._cache_dir.mkdir(parents=True, exist_ok=True)

                file = self._cache_dir / f"schema-{version}.json"
                if file.exists():
                    LOG.info(f"Reading schema from cache: {file}")
                    return from_file(str(file))
                else:
                    LOG.debug(f"Cache miss: {file}")

            # Ensure the version exists on the server.
            if version not in self.get_versions():
                raise ValueError(f"Version {version} not found on server")

        # Fetch the schema from the server.
        schema = self._fetch_schema(version)

        # Cache the schema.
        if self._cache_dir is not None:
            ver = Version.parse(schema.version)
            if ver.prerelease != "dev":
                dest = str(self._cache_dir / f"schema-{schema.version}.json")
                LOG.debug(f"Caching schema to {dest}")
                to_file(schema, dest)

        return schema
