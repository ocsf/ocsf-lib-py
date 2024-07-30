"""Compile a repository into a schema and dump it as JSON to STDOUT.

Valid command line arguments are:
```
positional arguments:
  path                  Path to the OCSF repository

options:
  -h, --help            show this help message and exit
  --profile [PROFILE ...]
                        The name of a profile to be enabled (defaults to all)
  --ignore-profile [IGNORE_PROFILE ...]
                        The name of a profile to be disabled
  --extension [EXTENSION ...]
                        The short path name (e.g. 'windows') of an extension to be enabled (defaults to all)
  --ignore-extension [IGNORE_EXTENSION ...]
                        The short path name of an extension to be disabled
  --prefix-extensions   Prefix object and event names and any attributes that reference them as their type with the extension name
  --no-prefix-extensions
                        Do not prefix object and event names and any attributes that reference them as their type with the extension name
  --set-object-types    Set type to 'object' and object_type to the object name for type references to objects
  --no-set-object-types
                        Do not set type to 'object' and object_type to the object name for type references to objects
  --set-observable      Set the observable field on attributes to the corresponding Observable Type ID where applicable
  --no-set-observable   Do not set the observable field on attributes to the corresponding Observable Type ID where applicable
```

Examples:

Build the schema:

    $ python -m ocsf.compile /path/to/repo

Build the schema with the data_security profile disabled:

    $ python -m ocsf.compile /path/to/repo --ignore-profile=data_security

Build the schema with only the windows extension enabled:

    $ python -m ocsf.compile /path/to/repo --extension=windows

"""

from argparse import ArgumentParser

from ocsf.repository import read_repo
from ocsf.schema import to_json

from .compiler import Compilation
from .options import CompilationOptions

def main():
    parser = ArgumentParser(description="Compile an OCSF repository into a schema and dump it as JSON to STDOUT")
    parser.add_argument("path", help="Path to the OCSF repository")
    parser.add_argument("--profile", nargs="*", help="The name of a profile to be enabled (defaults to all)")
    parser.add_argument("--ignore-profile", nargs="*", help="The name of a profile to be disabled")
    parser.add_argument(
        "--extension",
        nargs="*",
        help="The short path name (e.g. 'windows') of an extension to be enabled (defaults to all)",
    )
    parser.add_argument("--ignore-extension", nargs="*", help="The short path name of an extension to be disabled")
    parser.add_argument(
        "--prefix-extensions",
        default=True,
        action="store_true",
        help="Prefix object and event names and any attributes that reference them as their type with the extension name",
    )
    parser.add_argument(
        "--no-prefix-extensions",
        dest="prefix_extensions",
        action="store_false",
        help="Do not prefix object and event names and any attributes that reference them as their type with the extension name",
    )
    parser.add_argument(
        "--set-object-types",
        default=True,
        action="store_true",
        help="Set type to 'object' and object_type to the object name for type references to objects",
    )
    parser.add_argument(
        "--no-set-object-types",
        dest="set_object_types",
        action="store_false",
        help="Do not set type to 'object' and object_type to the object name for type references to objects",
    )
    parser.add_argument(
        "--set-observable",
        default=True,
        action="store_true",
        help="Set the observable field on attributes to the corresponding Observable Type ID where applicable",
    )
    parser.add_argument(
        "--no-set-observable",
        dest="set_observable",
        action="store_false",
        help="Do not set the observable field on attributes to the corresponding Observable Type ID where applicable",
    )

    args = parser.parse_args()

    options = CompilationOptions()

    if args.profile:
        options.profiles = args.profile
    if args.ignore_profile:
        options.ignore_profiles = args.ignore_profile
    if args.extension:
        options.extensions = args.extension
    if args.ignore_extension:
        options.ignore_extensions = args.ignore_extension

    options.prefix_extensions = args.prefix_extensions
    options.set_object_types = args.set_object_types
    options.set_observable = args.set_observable

    repo = read_repo(args.path, preserve_raw_data=False)
    compiler = Compilation(repo, options)

    print(to_json(compiler.build()))

if __name__ == "__main__":
    main()