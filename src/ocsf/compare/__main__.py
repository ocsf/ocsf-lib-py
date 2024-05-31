"""Compare OCSF schemata and print the differences.

Example:

    $ python -m ocsf_diff old_schema.json new_schema.json

"""

from argparse import ArgumentParser
from typing import cast

from ocsf.util import get_schema
from ocsf.schema import OcsfSchema

from .model import ChangedModel
from .compare import compare
from .formatter import format

if __name__ == "__main__":
    parser = ArgumentParser(description="Compare two OCSF schemata")

    parser.add_argument("old_schema", help="Path to the old schema file or the old schema version.")
    parser.add_argument("new_schema", help="Path to the new schema file or the new schema version.")

    args = parser.parse_args()

    old_schema = get_schema(args.old_schema)
    new_schema = get_schema(args.new_schema)

    delta = compare(old_schema, new_schema)
    format(cast(ChangedModel[OcsfSchema], delta))

