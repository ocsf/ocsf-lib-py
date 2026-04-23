import os

from ocsf.schema import OcsfEvent, SchemaOptions, from_json

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

V2_JSON_DATA = """{
    "version": "1.8.0",
    "classes": {},
    "objects": {},
    "dictionary": {
        "attributes": {
            "product": {
                "caption": "Product",
                "description": "The product that reported the event.",
                "type": "object_t",
                "object_type": "product",
                "object_name": "Product"
            },
            "raw_header": {
                "caption": "Raw Header",
                "description": "The email authentication header.",
                "type": "string_t",
                "type_name": "String"
            }
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
                    "observable": 5
                },
                "uuid_t": {
                    "caption": "UUID",
                    "description": "Universal unique identifier.",
                    "regex": "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}",
                    "type": "string_t",
                    "type_name": "String"
                }
            }
        },
        "caption": "Dictionary"
    },
    "categories": {
        "attributes": {
            "system": {
                "uid": 1,
                "caption": "System Activity"
            }
        },
        "name": "categories",
        "description": "Categories",
        "caption": "Categories"
    },
    "profiles": {
        "trace": {
            "meta": "profile",
            "name": "trace",
            "description": "Trace profile",
            "caption": "Trace"
        }
    },
    "extensions": {
        "linux": {
            "name": "linux",
            "uid": 1,
            "caption": "Linux",
            "platform_extension?": true
        }
    },
    "compile_version": "2.0.0"
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
    with open(SCHEMA_JSON) as f:
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


def test_decode_v2_schema_payload():
    schema = from_json(V2_JSON_DATA)

    assert "email_t" in schema.types
    assert schema.types["email_t"].type == "string_t"
    assert schema.types["email_t"].type_name == "String"
    assert "uuid_t" in schema.types
    assert schema.types["uuid_t"].type == "string_t"
    assert schema.types["uuid_t"].type_name == "String"
    assert "product" not in schema.types
    assert "raw_header" not in schema.types
    assert schema.categories is not None
    assert "system" in schema.categories
    assert schema.categories["system"].name == "system"
    assert schema.profiles is None
    assert schema.extensions is not None
    assert "linux" in schema.extensions
