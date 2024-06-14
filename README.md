# OCSF Library for Python

Tools for building Python scripts and applications leveraging the OCSF.

## About

This project began with two goals:

1. Provide the OCSF community with a validator that tests for breaking changes
   in `ocsf-schema` PRs.
2. Begin to provide the OCSF community with more composable tools and libraries,
   as well as approachable reference implementations of OCSF related functions, in
   order to make OCSF more "hackable."

The scope of this project may grow to include things like a reference
implementation OCSF schema compiler.

The project targets Python 3.11 for a balance of capability and availability.
The root level package, `ocsf`, is a namespace package so that other
repositories and artifacts can also use the `ocsf` namespace.

This library is divided into several discrete packages.

### ocsf.util: The utilities package

The `ocsf.util` package provides the `get_schema` function. This function
leverages the functionality in the `ocsf.schema` and `ocsf.api` packages (below)
to easily build an OCSF schema from a file on disk or from the API.

```python
schema = get_schema("1.1.0")
schema = get_schema("./1.3.0-dev.json")
```

### ocsf.schema: The Schema Package

The `ocsf.schema` package contains Python data classes that represent an
OCSF schema as represented from the OCSF server's API endpoints. See the
`ocsf.schema.model` module for the data model definitions.

It also includes utilities to parse the schema from a JSON string or file.

### ocsf.api: The API Package

The `ocsf.api` package exports an `OcsfApiClient`, which is a lightweight HTTP
client that can retrieve a version of the schema over HTTP and cache it on the
local filesystem. It uses thes `export/schema`, `api/versions`, `api/profiles`,
and `api/extensions` endpoints of the OCSF server.

### ocsf.compare: The Compare Package

The `ocsf_tools.compare` package compares two versions of the OCSF schema and
generates a type safe difference. Its aim is to make schema comparisons easy to
work with.

This package grew out of a library used internally at [Query](https://query.ai).
The original is used extensively to manage upgrading Query's data model to newer
versions of OCSF, as well as to build adapters between different OCSF flavors
(like AWS Security Lake on rc2 and Query on 1.1).

There is a very simple `__main__` implementation to demonstrate the comparison.
You can use it as follows:

```sh
$ poetry run python -m ocsf_tools.compare 1.0.0 1.2.0
```

The comparison API is straightforward. Want to look for removed events?

```python
diff = compare(get_schema("1.0.0", "1.1.0"))
for name, event in diff.classes.items():
    if isinstance(event, Removal):
        print(f"Oh no, we've lost {name}!")
```

Or changed data types?

```python
diff = compare(get_schema("1.0.0", "1.1.0"))
for name, event in diff.classes.items():
    if isinstance(event, ChangedEvent):
        for attr_name, attr in event.attributes.items():
            if isinstance(attr, ChangedAttr):
                if isinstance(attr.type, Change):
                    print(f"Who changed this data type? {name}.{attr_name}")
```

Or new objects?

```python
diff = compare(get_schema("1.0.0", "1.1.0"))
for name, obj in diff.objects.items():
    if isinstance(obj, Addition):
        print(f"A new object {name} has been discovered!")
```


### ocsf.validate.framework: The Validation Framework Package 

The `ocsf.valide.framework` package provides a lightweight framework for
validators. It was inspired by the needs of `ocsf-validator`, which may be
ported to this framework in the future.


## Getting Started

### PyPI

The easiest way to install `ocsf-lib` is from PyPI using `pip` or `poetry`:

```sh
$ pip install ocsf-lib
```


### From Source

If you want to work with the source, the recommended installation is with `asdf`
and `poetry`.

```sh
$ asdf install
$ poetry install
```

## Contributing

This project uses `ruff` for formatting and linting, `pyright` for type
checking, and `pytest` as its test runner.

Before submitting a PR, make sure you've run following:

```sh
$ poetry run ruff format
$ poetry run ruff check
$ poetry run pyright
$ poetry run pytest
```

### Type Checking

With great effort, this library passes pyright's strict mode type checking. Keep
it that way! The OCSF schema is big, and even the metaschema is a lot to hold in
your head. Having the type checker identify mistakes for you can be very
helpful.

There is one cast used from the concrete `ChangedModel` types (`ChangedSchema`,
`ChangedAttr`, etc.) in the compare package to the generic type. For the life of
me, I can't figure it out. I blame pyright but it's probably my own fault.

### Tests

Running unit tests:

```sh
$ poetry run pytest -m "not integration"
```

Running integration tests:

```sh
$ poetry run pytest -m integration
```

**NOTE**: Some of the integration tests require an OCSF server instance, and are
using the public instance at [https://schema.ocsf.io](https://schema.ocsf.io).
This should probably use a local instance of the OCSF server instead.
