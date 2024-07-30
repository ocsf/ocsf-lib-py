import os
import pytest

from ocsf.api import OcsfApiClient
from ocsf.schema import OcsfSchema
from ocsf.util import get_schema


LOCATION = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(LOCATION, "../../..", "schema_cache")
REPO = os.environ["COMPILE_REPO_PATH"]




def test_get_schema_file():
    """Test fetching a schema from a file."""
    schema = get_schema(os.path.join(CACHE, "schema-1.1.0.json"))
    assert isinstance(schema, OcsfSchema)
    assert schema.version == "1.1.0"
    assert len(schema.classes) > 0
    assert len(schema.objects) > 0


def test_get_schema_version_cache():
    """Test fetching a schema by version from the cache."""
    # This schema is known to be cached
    schema = get_schema("1.1.0", OcsfApiClient(cache_dir=CACHE))
    assert isinstance(schema, OcsfSchema)
    assert schema.version == "1.1.0"
    assert len(schema.classes) > 0
    assert len(schema.objects) > 0

def test_get_schema_repo():
    """Test fetching a schema from a repository."""
    schema = get_schema(REPO)
    assert isinstance(schema, OcsfSchema)
    assert schema.version == "1.2.0"
    assert len(schema.classes) > 0
    assert len(schema.objects) > 0

@pytest.mark.integration
def test_get_schema_version_server():
    """Test fetching a schema by version from the server."""
    # By not passing get_schema() a client, there won't be a cache
    schema = get_schema("1.1.0")
    assert isinstance(schema, OcsfSchema)
    assert schema.version == "1.1.0"
    assert len(schema.classes) > 0
    assert len(schema.objects) > 0
