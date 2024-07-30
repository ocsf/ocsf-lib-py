"""
This module is the entry point for the compatibility tool.

Most of what you'll find here is glue code to combine configuration from CLI
arguments and an optional TOML file. Skip to the bottom to see a validator
initialized and run.

This module uses `get_schema` to load the schemas to be compared from either a
local file or, if a version number is used, the OCSF server (or a cached copy).

Valid TOML configuration options are:
- before: The path or version of the "before" schema.
- after: The path or version of the "after" schema.
- cache: The path to the schema cache directory.
- severity: A dictionary of finding names to severities. Severity may be one of
  "info", "warning", "error", or "fatal".

See example.toml for an example configuration file.

Valid command line arguments are:
```
options:
  -h, --help            show this help message and exit
  --before BEFORE, -b BEFORE
                        Path to the schema file before the change
  --after AFTER, -a AFTER
                        Path to the schema file before the change
  --cache CACHE         Path to the schema cache directory
  --config CONFIG       Path to the config.toml file
  --info [INFO ...]     A finding to assign an info severity to
  --warning [WARNING ...]
                        A finding to assign an warning severity to
  --error [ERROR ...]   A finding to assign an error severity to
  --fatal [FATAL ...]   A finding to assign an fatal severity to
```

Examples:

Validate a schema defined in a file is compatible with 1.0.0 from the OCSF server:

    $ python -m ocsf_tools.compatibility --after ./schema.json --before 1.0.0


Validate two schema versions available from the OCSF server with a local cache:

    $ python -m ocsf_tools.compatibility --before 1.0.0 --after 1.1.0 --cache ./schema_cache

Validate schemata using a configuration file:

    $ python -m ocsf_tools.compatibility --config ./config.toml

Validate schemata but don't worry about removed enum members:

    $ python -m ocsf_tools.compatibility --config ./config.toml --info RemovedEnumMember

Validate a working copy of the OCSF schema repository against the latest stable version:

    $ python -m ocsf_tools.compatibility --before latest-stable --after ./src/ocsf-schema

"""

import tomllib
from argparse import ArgumentParser
from typing import cast
from urllib.error import URLError
from termcolor import colored

from ocsf.api import OcsfApiClient
from ocsf.util import get_schema
from ocsf.validate.framework import (
    Severity,
    ColoringValidationFormatter,
    ValidationFormatter,
    validate_severities,
    count_severity,
)
from ocsf.compare import compare, ChangedSchema

from .validator import CompatibilityValidator


# Various modules use logging. Configure as you see fit.
# import logging
# import sys
# logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)


def main():
    # Default configuration
    config = {
        "before": "1.0.0",
    }

    # Default finding names x severities
    severities: dict[str, Severity] = {}

    # Configure parser
    parser = ArgumentParser(description="Validate compatibility between two OCSF schemas")
    parser.add_argument(
        "before",
        nargs="?",
        default="latest-stable",
        help="Path or version number of the old schema. Defaults to 'latest-stable'.",
    )
    parser.add_argument("after", help="Path or version number of the new schema.")
    parser.add_argument("--cache", help="Path to the schema cache directory.")
    parser.add_argument("--config", help="Path to the config.toml file.")
    parser.add_argument("--info", nargs="*", action="append", help="A finding to assign an info severity to.")
    parser.add_argument("--warning", nargs="*", action="append", help="A finding to assign a warning severity to.")
    parser.add_argument("--error", nargs="*", action="append", help="A finding to assign an error severity to.")
    parser.add_argument("--fatal", nargs="*", action="append", help="A finding to assign a fatal severity to.")
    parser.add_argument("--color", action="store_true", default=True, help="Enable colored output.")
    parser.add_argument("--no-color", dest="color", action="store_false", help="Enable colored output.")
    parser.add_argument("--url", help="URL of the OCSF server.")
    parser.add_argument("--before-url", help="URL of the OCSF server used to fetch the old schema.")
    parser.add_argument("--after-url", help="URL of the OCSF server used to fetch the new schema.")

    args = parser.parse_args()

    # Read configuration from file
    if args.config:
        with open(args.config, "rb") as f:
            conf = tomllib.load(f)

            if "before" in conf:
                config["before"] = conf["before"]
            if "after" in conf:
                config["after"] = conf["after"]
            if "cache" in conf:
                config["cache"] = conf["cache"]
            if "severity" in conf:
                sevs = conf["severity"]
                if isinstance(sevs, dict):
                    severities |= cast(dict[str, Severity], sevs)
            if "before_url" in conf:
                config["before_url"] = conf["before_url"]
            if "after_url" in conf:
                config["after_url"] = conf["after_url"]
            if "url" in conf:
                config["url"] = conf["url"]

    # Override configuration from command line arguments
    if args.before:
        config["before"] = args.before
    if args.before_url:
        config["before_url"] = args.before_url

    if args.after:
        config["after"] = args.after
    if args.after_url:
        config["after_url"] = args.after_url

    if args.url:
        config["url"] = args.url

    if args.cache:
        config["cache"] = args.cache

    if args.info:
        for finding in args.info:
            for f in finding:
                severities[f] = Severity.INFO

    if args.warning:
        for finding in args.warning:
            for f in finding:
                severities[f] = Severity.WARNING

    if args.error:
        for finding in args.error:
            for f in finding:
                severities[f] = Severity.ERROR

    if args.fatal:
        for finding in args.fatal:
            for f in finding:
                severities[f] = Severity.FATAL

    # Check severity names
    validate_severities(severities)

    # Enforce that before and after are present
    if "before" not in config:
        print("Missing before schema file or version")
        exit(1)

    if "after" not in config:
        print("Missing after schema file or version")
        exit(1)

    # Load the schemas
    try:
        client = OcsfApiClient(
            cache_dir=config.get("cache", None), base_url=config.get("before_url", config.get("url", None))
        )
        before = get_schema(config["before"], client)
    except URLError:
        print("Unable to communicate with the OCSF server to fetch the old schema.")
        exit(1)

    try:
        client = OcsfApiClient(
            cache_dir=config.get("cache", None), base_url=config.get("after_url", config.get("url", None))
        )
        after = get_schema(config["after"], client)
    except URLError:
        print("Unable to communicate with the OCSF server to fetch the new schema.")
        exit(1)

    # Configure a validator and run it
    validator = CompatibilityValidator(cast(ChangedSchema, compare(before, after)), severities)
    results = validator.validate()

    print()
    if not args.color:
        print(" OCSF Compatibility Validator ")
        print("=" * 30)
    else:
        print(colored(" OCSF Compatibility Validator", "white"))
        print(colored("=" * 30, "magenta"))

    print()
    print("Validate backwards compatibility between two OCSF schemas.\n")
    print(
        "For more information about breaking changes in OCSF, see the Schema FAQ:\n  https://github.com/ocsf/ocsf-docs/blob/main/FAQs/Schema%20FAQ.md\n"
    )

    print(f"Looking for breaking changes between ocsf-schema-{before.version} and ocsf-schema-{after.version}.")
    print()

    # Initialize a formatter
    if not args.color:
        formatter = ValidationFormatter()
    else:
        formatter = ColoringValidationFormatter()

    # Show the results
    print(formatter.format(results))

    # Exit with an error code if there are any errors or fatal findings
    if count_severity(results, Severity.ERROR) > 0 or count_severity(results, Severity.FATAL) > 0:
        exit(2)


if __name__ == "__main__":
    main()
