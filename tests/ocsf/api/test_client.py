import pytest

from ocsf.api import OcsfApiClient
from ocsf.schema.model import OcsfSchema

from semver import Version


def setup() -> OcsfApiClient:
    return OcsfApiClient()


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


@pytest.mark.integration
def test_get_schema_version():
    """Test fetching the schema from the OCSF server with a version number."""
    s = setup().get_schema("1.2.0")
    assert isinstance(s, OcsfSchema)
    assert s.version == "1.2.0"
    assert len(s.classes) == 65
    assert len(s.objects) == 111
