import pytest

from ocsf.api import OcsfApiClient
from ocsf.schema.model import OcsfSchema, OcsfProfile, OcsfExtension

from semver import Version


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
