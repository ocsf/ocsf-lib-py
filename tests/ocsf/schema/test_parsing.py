import os
from ocsf.schema import OcsfEvent, from_json, SchemaOptions

LOCATION = os.path.dirname(os.path.abspath(__file__))
SCHEMA_JSON = os.path.join(LOCATION, "../..", "schema_cache/schema-1.1.0.json")

JSON_DATA = """{
  "version": "1.0",
  "classes": {
    "authentication": {
        "name": "authentication",
        "description": "An authentication attempt",
        "category": "iam",
        "caption": "Authentication",
        "attributes": {
            "status": {
                "caption": "Status",
                "type": "int_t",
                "requirement": "required",
                "description": "Auth status"
            }
        }
    }
  },
  "objects": {
  
  },
  "types": {

  },
  "base_event": {
    "name": "base_event",
    "description": "Base event",
    "category": "base",
    "caption": "Base",
    "attributes": {
        "timestamp": {
            "type": "int_t",
            "caption": "Timestamp",
            "requirement": "required",
            "description": "Event timestamp"
        }
    }
  
  }
}"""


def test_decode_str():
    """Test decoding a JSON string into an OCSF schema."""
    schema = from_json(JSON_DATA)
    assert len(schema.classes) > 0
    assert "authentication" in schema.classes
    assert isinstance(schema.classes["authentication"], OcsfEvent)


def test_decode_file():
    """Test decoding a JSON file into an OCSF schema."""
    json_str: str | None = None
    with open(SCHEMA_JSON, "r") as f:
        json_str = f.read()
    assert json_str is not None
    schema = from_json(json_str)

    assert len(schema.classes) > 0
    assert "authentication" in schema.classes
    assert isinstance(schema.classes["authentication"], OcsfEvent)


def test_no_resolve_object_types():
    json_str = """{
        "version": "1.0.0",
        "types": { },
        "objects": {
            "stuff": {
                "name": "stuff",
                "caption": "Stuff",
                "attributes": { }
            }
        },
        "classes": {
            "event": {
                "name": "event",
                "caption": "Event",
                "attributes": {
                    "thing": {
                        "caption": "Thing",
                        "type": "object_t",
                        "requirement": "required",
                        "description": "An object",
                        "object_type": "stuff"
                    }
                }
            }
        }
    }"""

    schema = from_json(json_str, SchemaOptions(resolve_object_types=True))
    assert "event" in schema.classes
    assert schema.classes["event"].attributes["thing"].type == "stuff"

    schema = from_json(json_str, SchemaOptions(resolve_object_types=False))
    assert "event" in schema.classes
    assert schema.classes["event"].attributes["thing"].type == "object_t"
