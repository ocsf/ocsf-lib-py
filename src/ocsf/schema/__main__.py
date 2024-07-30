"""Dump an OCSF schema as JSON to STDOUT from a variety of input sources.

Example:

    $ python -m ocsf.schema path/to/schema
    $ python -m ocsf.schema 1.2.0
    $ python -m ocsf.schema schema.json

"""

from argparse import ArgumentParser

from ocsf.util import get_schema
from ocsf.schema import to_json


def main():
    parser = ArgumentParser(description="Dump an OCSF schema as JSON to STDOUT")

    parser.add_argument("schema", help="Path to a schema JSON file, a version identifier (to retrieve from schema.ocsf.io), or a path to an OCSF repository.")
    args = parser.parse_args()

    print(to_json(get_schema(args.schema)))


if __name__ == "__main__":
    main()
