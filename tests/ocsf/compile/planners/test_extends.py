from ocsf.repository import Repository, DefinitionFile, AttrDefn, EventDefn
from ocsf.compile.protoschema import ProtoSchema
from ocsf.compile.options import CompilationOptions
from ocsf.compile.planners.extends import ExtendsPlanner, ExtendsOp
from ocsf.compile.planners.extends import _find_base  # type: ignore


def get_repo():
    repo = Repository()
    repo["events/base.json"] = DefinitionFile(
        "events/base.json", data=EventDefn(attributes={"a": AttrDefn(description="A!")})
    )
    repo["events/network/network.json"] = DefinitionFile(
        "events/network/network.json", data=EventDefn(extends="base", attributes={"b": AttrDefn(description="B!")})
    )
    repo["events/network/ssh_activity.json"] = DefinitionFile(
        "events/network/ssh_activity.json",
        data=EventDefn(extends="network", attributes={"c": AttrDefn(description="C!")}),
    )
    repo["extensions/win/events/network/cifs_activity.json"] = DefinitionFile(
        "extensions/win/events/network/cifs_activity.json",
        data=EventDefn(extends="network", attributes={"d": AttrDefn(description="D!")}),
    )

    return repo


def get_schema():
    return ProtoSchema(get_repo())


def get_planner(ps: ProtoSchema):
    return ExtendsPlanner(ps, CompilationOptions())


def test_apply():
    ps = get_schema()
    op = ExtendsOp("events/network/network.json", "events/base.json")
    result = op.apply(ps)
    assert len(result) == 1
    assert result[0] == ("attributes", "a")
    assert isinstance(ps["events/network/network.json"].data, EventDefn)
    assert ps["events/network/network.json"].data.attributes == {
        "a": AttrDefn(description="A!"),
        "b": AttrDefn(description="B!"),
    }


def test_find_base():
    repo = get_repo()
    assert _find_base(repo, "base", "events/network/network.json") == "events/base.json"
    assert _find_base(repo, "base", "events/network/ssh_activity.json") == "events/base.json"
    assert _find_base(repo, "network", "events/network/ssh_activity.json") == "events/network/network.json"
    assert (
        _find_base(repo, "network", "extensions/win/events/network/cifs_activity.json") == "events/network/network.json"
    )


def test_analyze_positive():
    ps = get_schema()
    planner = get_planner(ps)

    op = planner.analyze(ps["events/network/network.json"])
    assert isinstance(op, ExtendsOp)
    assert op.target == "events/network/network.json"
    assert op.prerequisite == "events/base.json"


def test_analyze_negative():
    ps = get_schema()
    planner = get_planner(ps)

    op = planner.analyze(ps["events/base.json"])
    assert op is None
