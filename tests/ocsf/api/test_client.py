import json
from email.message import Message
from io import BytesIO
from urllib.error import HTTPError

import pytest
from semver import Version

import ocsf.api.client as client_module
from ocsf.api import OcsfApiClient, SchemaVersion, SchemaVersions
from ocsf.schema.model import OcsfExtension, OcsfProfile, OcsfSchema


class Response:
    def __init__(self, payload: bytes):
        self._payload = payload

    def read(self) -> bytes:
        return self._payload


def schema_payload(version: str) -> bytes:
    return json.dumps({"version": version, "classes": {}, "objects": {}, "types": {}}).encode()


def v2_schema_payload(version: str) -> bytes:
    return json.dumps(
        {
            "version": version,
            "classes": {},
            "objects": {},
            "dictionary": {
                "attributes": {
                    "product": {
                        "caption": "Product",
                        "description": "The product that reported the event.",
                        "type": "object_t",
                        "object_type": "product",
                        "object_name": "Product",
                    },
                    "raw_header": {
                        "caption": "Raw Header",
                        "description": "The email authentication header.",
                        "type": "string_t",
                        "type_name": "String",
                    },
                },
                "name": "dictionary",
                "description": "Dictionary",
                "types": {
                    "attributes": {
                        "email_t": {
                            "caption": "Email Address",
                            "description": "Email address.",
                            "type": "string_t",
                            "type_name": "String",
                            "observable": 5,
                        },
                        "uuid_t": {
                            "caption": "UUID",
                            "description": "Universal unique identifier.",
                            "regex": "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
                            "type": "string_t",
                            "type_name": "String",
                        },
                    }
                },
                "caption": "Dictionary",
            },
            "extensions": {
                "linux": {
                    "name": "linux",
                    "uid": 1,
                    "caption": "Linux",
                }
            },
        }
    ).encode()


def setup() -> OcsfApiClient:
    return OcsfApiClient(fetch_profiles=False, fetch_extensions=False)


@pytest.mark.integration
def test_get_versions():
    """Test fetching versions from the OCSF server."""
    versions = setup().get_versions()

    assert isinstance(versions, list)
    assert len(versions) > 0
    assert "1.0.0" in versions
    assert "1.1.0" in versions
    assert "1.2.0" in versions


@pytest.mark.integration
def test_get_schema_default():
    """Test fetching the schema from the OCSF server without a version number."""
    s = setup().get_schema()
    assert isinstance(s, OcsfSchema)
    assert isinstance(Version.parse(s.version), Version)
    assert len(s.classes) > 0
    assert len(s.objects) > 0
    assert s.profiles is None
    assert s.extensions is None


@pytest.mark.integration
def test_get_schema_latest():
    """Test fetching the schema from the OCSF server using version keywords."""
    s = setup().get_schema(SchemaVersion.LATEST)
    assert isinstance(s, OcsfSchema)
    assert isinstance(Version.parse(s.version), Version)
    assert len(s.classes) > 0
    assert len(s.objects) > 0
    assert s.profiles is None
    assert s.extensions is None

    s = setup().get_schema(SchemaVersion.LATEST_STABLE)
    assert isinstance(s, OcsfSchema)
    assert isinstance(Version.parse(s.version), Version)
    assert len(s.classes) > 0
    assert len(s.objects) > 0
    assert s.profiles is None
    assert s.extensions is None


@pytest.mark.integration
def test_get_schema_version():
    """Test fetching the schema from the OCSF server with a version number."""
    s = setup().get_schema("1.2.0")
    assert isinstance(s, OcsfSchema)
    assert s.version == "1.2.0"
    assert len(s.classes) == 65
    assert len(s.objects) == 111
    assert s.profiles is None
    assert s.extensions is None


@pytest.mark.integration
@pytest.mark.parametrize("version", ["1.7.0", "1.8.0"])
def test_get_schema_version_boundary(version: str):
    """Test fetching schema versions on both sides of the export boundary."""
    s = setup().get_schema(version)

    assert isinstance(s, OcsfSchema)
    assert s.version == version
    assert len(s.classes) > 0
    assert len(s.objects) > 0
    assert s.profiles is None
    assert s.extensions is None


@pytest.mark.integration
def test_get_profiles():
    """Test fetching profiles from the OCSF server."""
    profiles = setup().get_profiles("1.2.0")
    assert len(profiles) == 9
    assert "cloud" in profiles
    assert isinstance(profiles["cloud"], OcsfProfile)
    assert len(profiles["cloud"].attributes) == 2

    schema = OcsfApiClient(fetch_profiles=True).get_schema("1.2.0")
    assert schema.profiles == profiles


@pytest.mark.integration
def test_get_extensions():
    """Test fetching extensions from the OCSF server."""
    extensions = setup().get_extensions("1.2.0")
    assert len(extensions) == 2
    assert "linux" in extensions
    assert isinstance(extensions["linux"], OcsfExtension)
    assert "win" in extensions
    assert isinstance(extensions["win"], OcsfExtension)


def test_latest_version():
    """Test fetching the latest version from the OCSF server."""
    version_list = [
        SchemaVersion(version="1.0.0"),
        SchemaVersion(version="1.2.0"),
        SchemaVersion(version="1.1.0"),
        SchemaVersion(version="1.3.0-dev"),
    ]
    versions = SchemaVersions(default=SchemaVersion(version="1.2.0"), versions=version_list)

    assert versions.latest().version == "1.3.0-dev"
    assert versions.latest_stable().version == "1.2.0"


@pytest.mark.parametrize(
    ("version", "expected_url"),
    [
        ("1.7.0", "https://schema.ocsf.io/1.7.0/export/schema"),
        ("1.8.0", "https://schema.ocsf.io/1.8.0/export/v2/schema"),
    ],
)
def test_fetch_schema_uses_versioned_export_endpoint(monkeypatch: pytest.MonkeyPatch, version: str, expected_url: str):
    requested_urls: list[str] = []

    def fake_urlopen(url: str) -> Response:
        requested_urls.append(url)
        return Response(schema_payload(version))

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)

    schema = OcsfApiClient(fetch_profiles=False, fetch_extensions=False, fetch_categories=False)._fetch_schema(version)

    assert schema.version == version
    assert requested_urls == [expected_url]


def test_get_schema_uses_default_version_export_endpoint(monkeypatch: pytest.MonkeyPatch):
    versions = SchemaVersions(
        default=SchemaVersion(version="1.8.0"),
        versions=[SchemaVersion(version="1.7.0"), SchemaVersion(version="1.8.0")],
    )
    requested_urls: list[str] = []

    def fake_fetch_versions(self: OcsfApiClient) -> SchemaVersions:
        return versions

    def fake_urlopen(url: str) -> Response:
        requested_urls.append(url)
        return Response(schema_payload("1.8.0"))

    monkeypatch.setattr(OcsfApiClient, "_fetch_versions", fake_fetch_versions)
    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)

    schema = OcsfApiClient(fetch_profiles=False, fetch_extensions=False, fetch_categories=False).get_schema()

    assert schema.version == "1.8.0"
    assert requested_urls == ["https://schema.ocsf.io/1.8.0/export/v2/schema"]


def test_fetch_schema_includes_http_error_body(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(url: str) -> Response:
        raise HTTPError(url, 400, "Bad Request", hdrs=Message(), fp=BytesIO(b'{"error":"legacy format failure"}'))

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)

    client = OcsfApiClient(fetch_profiles=False, fetch_extensions=False, fetch_categories=False)
    with pytest.raises(ValueError, match="legacy format failure"):
        client._fetch_schema("1.8.0")


def test_fetch_schema_omits_embedded_v2_extensions_when_disabled(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(url: str) -> Response:
        return Response(v2_schema_payload("1.8.0"))

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)

    schema = OcsfApiClient(fetch_profiles=False, fetch_extensions=False, fetch_categories=False)._fetch_schema("1.8.0")

    assert schema.extensions is None


def test_fetch_schema_uses_v2_data_types_registry(monkeypatch: pytest.MonkeyPatch):
    def fake_urlopen(url: str) -> Response:
        return Response(v2_schema_payload("1.8.0"))

    monkeypatch.setattr(client_module, "urlopen", fake_urlopen)

    schema = OcsfApiClient(fetch_profiles=False, fetch_extensions=False, fetch_categories=False)._fetch_schema("1.8.0")

    assert schema.types["email_t"].type == "string_t"
    assert schema.types["email_t"].type_name == "String"
    assert schema.types["uuid_t"].type == "string_t"
    assert schema.types["uuid_t"].type_name == "String"
    assert "product" not in schema.types
    assert "raw_header" not in schema.types
