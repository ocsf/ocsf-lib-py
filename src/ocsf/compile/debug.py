

from argparse import ArgumentParser
from pprint import pprint

from ocsf.repository import read_repo

from .compiler import Compilation
from .planners.planner import Operation
from .merge import MergeResult

def find_prereqs(compilation: Compilation, file: str, found: set[str] | None = None) -> set[str]:
    if found is None:
        found = set()
    for phase in compilation.analyze():
        if file in phase:
            for op in phase[file]:
                if op.prerequisite is not None and op.prerequisite not in found:
                    found.add(op.prerequisite)
                    found |= find_prereqs(compilation, op.prerequisite, found)
    return found

def operations(compilation: Compilation, file: str | None = None, prereqs: bool = True):
    if prereqs and file is not None:
        files = find_prereqs(compilation, file)
        files.add(file)
    elif file is not None:
        files = set()
        files.add(file)
    else:
        files: set[str] = set()

    order = compilation.order()
    for op in order:
        if file is None or op.target in files:
            print(str(op))

def mutations(compilation: Compilation, file: str | None = None, prereqs: bool = True):
    if prereqs and file is not None:
        files = find_prereqs(compilation, file)
        files.add(file)
    elif file is not None:
        files = set()
        files.add(file)
    else:
        files: set[str] = set()

    compiled = compilation.compile()
    mutations: dict[Operation, MergeResult] = {}
    for f in files:
        if file is None or f in files:
            if f in compiled:
                for mutation in compiled[f]:
                    if len(mutation[1]) > 0:
                        mutations[mutation[0]] = mutation[1]

    ordered = compilation.order()
    for op in ordered:
        if op in mutations:
            print(str(op))
            pprint(mutations[op])
            print()

def main():
    parser = ArgumentParser(description="Debugging tool for OCSF compilation")
    parser.add_argument("path", help="Path to the OCSF repository")
    parser.add_argument("--file", default=None, help="Narrow output to operations involving <file>.")
    parser.add_argument("--prereqs", action="store_true", default=False, help="Include operations on prerequisites of <file>.")
    parser.add_argument("--changes", action="store_true", default=True, help="Show changed properties as well as operations.")
    parser.add_argument("--no-changes", action="store_false", dest="changes", help="Show only operations.")

    args = parser.parse_args()

    compilation = Compilation(read_repo(args.path))
    file = args.file
    prereqs = args.prereqs

    if args.changes:
        mutations(compilation, file, prereqs)
    else:
        operations(compilation, file, prereqs)

if __name__ == "__main__":
    main()