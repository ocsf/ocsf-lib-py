import os

from ocsf.compile.compiler import Compilation
from ocsf.repository import read_repo


def test_resource_details_observable():
    assert "COMPILE_REPO_150" in os.environ, "Missing configuration for OCSF 1.5.0 repository path"
    comp = Compilation(read_repo(os.environ["COMPILE_REPO_150"]))
    schema = comp.build()

    assert "resource_details" in schema.objects, "resource_details object not found in schema"
    assert "observable" in schema.objects
    assert "type_id" in schema.objects["observable"].attributes, "type_id attribute is missing in observable object"
    assert schema.objects["observable"].attributes["type_id"].enum is not None, "Missing type_id enum"
    assert "38" in schema.objects["observable"].attributes["type_id"].enum, "Missing observable type_id=38"
    rd = schema.objects["observable"].attributes["type_id"].enum["38"]

    assert (
        rd.caption == "Resource Details Object: name"
    ), "Caption for type_id=38 should be 'Resource Details Object: name'"
