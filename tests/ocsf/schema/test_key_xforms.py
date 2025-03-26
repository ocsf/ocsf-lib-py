from ocsf.schema.json import keys_to_names, names_to_keys


def test_names_to_keys():
    data = {
        "foo": "bar",
        "deprecated": {
            "since": "blah",
            "message": "meh",
        },
        "baz": {
            "qux": "quux",
            "include_": "grault",
        },
    }

    assert names_to_keys(data) == {
        "foo": "bar",
        "@deprecated": {
            "since": "blah",
            "message": "meh",
        },
        "baz": {
            "qux": "quux",
            "$include": "grault",
        },
    }


def test_keys_to_names():
    data = {
        "foo": "bar",
        "@deprecated": {
            "since": "blah",
            "message": "meh",
        },
        "baz": {
            "qux": "quux",
            "$include": "grault",
        },
    }

    assert keys_to_names(data) == {
        "foo": "bar",
        "deprecated": {
            "since": "blah",
            "message": "meh",
        },
        "baz": {
            "qux": "quux",
            "include_": "grault",
        },
    }
