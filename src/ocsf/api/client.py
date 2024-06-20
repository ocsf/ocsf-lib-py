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
from typing import Optional, Any, cast, ClassVar
from semver import Version
from pathlib import Path

from dacite import from_dict

from ocsf.schema import (
    OcsfSchema,
    OcsfProfile,
    OcsfExtension,
    SchemaOptions,
    WithAttributes,
    from_json,
    from_file,
    to_file,
    resolve_object_types,
)


LOG = logging.getLogger(__name__)


def _is_semver(version: str) -> bool:
    """Is a version string a valid semantic version?"""
    try:
        Version.parse(version)
        return True
    except ValueError:
        return False


def _semver_sort_key(version: Version) -> int:
    """Return a sort key for a semantic version."""
    return version.major * 1000 + version.minor * 10 + version.patch


# Models representing the response from the OCSF server's /api/versions endpoint.
@dataclass
class SchemaVersion:
    LATEST: ClassVar[str] = "latest"
    LATEST_STABLE: ClassVar[str] = "latest-stable"

    version: str
    url: str = ""

    def semver(self) -> Version:
        return Version.parse(self.version)


@dataclass
class SchemaVersions:
    default: SchemaVersion
    versions: list[SchemaVersion]

    def latest(self) -> SchemaVersion:
        return max(self.versions, key=lambda v: _semver_sort_key(v.semver()))

    def latest_stable(self) -> SchemaVersion:
        return max(
            (v for v in self.versions if v.semver().prerelease is None), key=lambda v: _semver_sort_key(v.semver())
        )


class OcsfApiClient:
    """A simple caching OCSF server client.

    This client uses a local filesystem cache to store schemas and avoid
    repeating requests to the OCSF server.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        cache_dir: Optional[str | Path] = None,
        schema_options: SchemaOptions = SchemaOptions(),
        fetch_profiles: bool = True,
        fetch_extensions: bool = True,
    ):
        """Create a new client.

        Args:
            base_url: The base URL of the OCSF server.
            cache_dir: The directory to store cached schemas in.
            schema_options: Options for Schema reification.
            fetch_profiles: If True, fetch available profiles when fetching a schema.
            fetch_extensions: If True, fetch available extensions when fetching a schema.
        """
        self._base_url = base_url or "https://schema.ocsf.io"
        self._versions: Optional[SchemaVersions] = None
        self._fetch_profiles = fetch_profiles
        self._fetch_extensions = fetch_extensions
        self._schema_options = schema_options

        if cache_dir is not None and not isinstance(cache_dir, Path):
            self._cache_dir = Path(cache_dir)
        else:
            self._cache_dir = cache_dir

    def _versioned_url(self, version: Optional[str] = None) -> str:
        """Get the URL for a specific schema version."""
        if version is not None:
            return urljoin(self._base_url, f"{version}/")
        else:
            return self._base_url

    def _fetch_schema(self, version: Optional[str] = None) -> OcsfSchema:
        """Fetch a schema from the server."""
        url = urljoin(self._versioned_url(version), "export/schema")

        LOG.debug(f"Fetching schema from {url} (version {version})")
        json_str = urlopen(url).read()
        return from_json(json_str, self._schema_options)

    def _fetch_versions(self) -> SchemaVersions:
        """Fetch the available versions from the server."""
        url = urljoin(self._base_url, "api/versions")
        data = json.loads(urlopen(url).read())
        return from_dict(SchemaVersions, data)

    def _resolve_version(self, version: str | None) -> str:
        """Resolve a version string to a specific version."""
        if version is None:
            return self.get_default_version()
        else:
            # Ensure versions are fetched
            self.get_versions()
            assert self._versions is not None

            if version == SchemaVersion.LATEST:
                return self._versions.latest().version
            elif version == SchemaVersion.LATEST_STABLE:
                return self._versions.latest_stable().version
            elif _is_semver(version):
                return version
            else:
                raise ValueError(f"Invalid version string: {version}")

    def get_profiles(self, version: Optional[str] = None) -> dict[str, OcsfProfile]:
        """Fetch the profiles for a specific schema version."""
        url = urljoin(self._versioned_url(version), "api/profiles")
        response = json.loads(urlopen(url).read())

        profiles: dict[str, OcsfProfile] = {}
        for name, data in cast(dict[str, dict[str, Any]], response).items():
            profiles[name] = from_dict(OcsfProfile, data)

        if self._schema_options.resolve_object_types:
            resolve_object_types(cast(dict[str, WithAttributes], profiles))
        return profiles

    def get_extensions(self, version: Optional[str] = None) -> dict[str, OcsfExtension]:
        """Fetch the extensions for a specific schema version."""
        url = urljoin(self._versioned_url(version), "api/extensions")
        response = json.loads(urlopen(url).read())

        extensions: dict[str, OcsfExtension] = {}
        for name, data in cast(dict[str, dict[str, Any]], response).items():
            extensions[name] = from_dict(OcsfExtension, data)

        return extensions

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
                default version is used. The keywords `latest` and `latest-stable`
                may also be used.

        Returns:
            The requested OcsfSchema.

        Raises:
            ValueError: If the version requested is not found on the server or
                if the requested version is invalid.
        """
        cached: Optional[OcsfSchema] = None

        if version is not None:
            # Ensure version is a valid semantic version string.
            version = self._resolve_version(version)

            # Check the cache first.
            if self._cache_dir is not None:
                if not self._cache_dir.exists():
                    LOG.debug(f"Creating cache directory: {self._cache_dir}")
                    self._cache_dir.mkdir(parents=True, exist_ok=True)

                file = self._cache_dir / f"schema-{version}.json"
                if file.exists():
                    LOG.info(f"Reading schema from cache: {file}")
                    cached = from_file(str(file), self._schema_options)
                else:
                    LOG.debug(f"Cache miss: {file}")

            # Ensure the version exists on the server.
            if version not in self.get_versions():
                raise ValueError(f"Version {version} not found on server")

        if cached is None:
            # Fetch the schema from the server.
            schema = self._fetch_schema(version)
        else:
            # Use the cached schema
            schema = cached

        if schema.profiles is None and self._fetch_profiles:
            # Fetch the profiles for the schema.
            schema.profiles = self.get_profiles(version)

        if schema.extensions is None and self._fetch_extensions:
            # Fetch the extensions for the schema.
            schema.extensions = self.get_extensions(version)

        # Cache the schema if caching is enabled and any of the following are true:
        #   - The schema is not cached
        #   - Profiles were retrieved from the OCSF server
        #   - Extensions were retrieved from the OCSF server
        if self._cache_dir is not None and (
            cached is None or cached.profiles != schema.profiles or cached.extensions != schema.extensions
        ):
            ver = Version.parse(schema.version)
            if ver.prerelease != "dev":
                dest = str(self._cache_dir / f"schema-{schema.version}.json")
                LOG.debug(f"Caching schema to {dest}")
                to_file(schema, dest)

        return schema
