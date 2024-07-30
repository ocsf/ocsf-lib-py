import os

from ocsf.repository import read_repo, Repository
from ocsf.compile.planners.planner import Operation
from ocsf.compile.compiler import Compilation, CompilationOperations


class OpTest1(Operation): ...


class OpTest2(Operation): ...


def get_compiler():
    return Compilation(read_repo(os.environ["COMPILE_REPO_PATH"]))


def test_analyze():
    compiler = get_compiler()
    analysis = compiler.analyze()
    assert len(analysis) == 4  # 4 phases

    assert "objects/databucket.json" in analysis[0]
    assert "objects/databucket.json" in analysis[2]


def test_order():
    ops: CompilationOperations = [
        {
            "c": [OpTest1(target="c", prerequisite="a")],
            "b": [OpTest1(target="b", prerequisite="a")],
            "a": [OpTest1(target="a", prerequisite=None)],
            "d": [OpTest1(target="d", prerequisite="c")],
        },
        {
            "a": [OpTest2(target="a", prerequisite=None)],
            "b": [OpTest2(target="b", prerequisite="a")],
        },
    ]

    compiler = Compilation(repo=Repository())
    order = compiler.order(ops)

    assert len(order) == 6
    assert order[0].target == "a"
    assert order[1].target == "c"
    assert order[2].target == "b"
    assert order[3].target == "d"
    assert order[4].target == "a"
    assert order[5].target == "b"


def test_order_live():
    compiler = get_compiler()
    analysis = compiler.analyze()
    order = compiler.order()

    c = 0
    for phase in analysis:
        for _, ops in phase.items():
            c += len(ops)

    # Same number of ops in ordered list as in analysis
    assert len(order) == c

    # No duplicate ops
    assert len(order) == len(set(order))
