# TODO this file is a stub for testing and should be converted into an example

from pprint import pprint
from ocsf.repository import read_repo

from .compiler import Compilation


PATH = "/Users/jfisher/Source/ocsf/ocsf-schema"

repo = read_repo(PATH, preserve_raw_data=True)
compiler = Compilation(repo)

# TARGET = "events/iam/authentication.json"
# TARGET = "events/base_event.json"
TARGET = "objects/process.json"
# TARGET = "extensions/windows/events/prefetch_query.json"
# TARGET = "includes/classification.json"

analysis = compiler.analyze()
order = compiler.order()
compile = compiler.compile()
schema = compiler.build()

print(f"TARGET: {TARGET}")
print("ORDER")
prereqs: set[str] = set()


def find_op(target: str):
    for o in order:
        if o.target == target and o.target not in prereqs:
            if o.prerequisite is not None and o.prerequisite not in prereqs:
                prereqs.add(o.prerequisite)
                find_op(o.prerequisite)
            # pprint(o)
    return None


find_op(TARGET)

for o in order:
    if o.target in prereqs or o.target == TARGET:
        pprint(o)
        if o.target in compile:
            for op, change in compile[o.target]:
                if op == o:
                    pprint(change)

# print()
# print("COMPILE")
#
# for prereq in prereqs:
#    if prereq in compile:
#        pprint(compile[prereq])
# pprint(compile[TARGET])
