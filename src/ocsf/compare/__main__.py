"""Compare OCSF schemata and print the differences.

Example:

    $ python -m ocsf.compare old_schema.json new_schema.json
    $ python -m ocsf.compare 1.2.0 new_schema.json
    $ python -m ocsf.compare new_schema.json path/to/ocsf-schema

"""

from argparse import ArgumentParser
from typing import cast
from termcolor import colored

from ocsf.util import get_schema
from ocsf.schema import OcsfSchema

from .model import ChangedModel
from .compare import compare
from .formatter import format


def main():
    parser = ArgumentParser(description="Compare two OCSF schemata")

    parser.add_argument("old_schema", help="Path to the old schema file, old schema repository, or the old schema version.")
    parser.add_argument("new_schema", help="Path to the new schema file, new schema repository, or the new schema version.")
    parser.add_argument(
        "--expand-changes",
        dest="collapse_changes",
        action="store_false",
        help="Expand changes as separate rows prefixed with +/- (default: collapse changes)",
    )
    parser.add_argument(
        "--collapse-changes",
        dest="collapse_changes",
        action="store_true",
        help="Show changes as a single row prefixed with ~ (default)",
    )

    args = parser.parse_args()

    old_schema = get_schema(args.old_schema)
    new_schema = get_schema(args.new_schema)
    collapse_changes = args.collapse_changes

    delta = compare(old_schema, new_schema)

    print(colored(f"--- {args.old_schema}:{old_schema.version}", "red"))
    print(colored(f"+++ {args.new_schema}:{new_schema.version}", "green"))
    format(cast(ChangedModel[OcsfSchema], delta), collapse_changes=collapse_changes)


if __name__ == "__main__":
    main()
