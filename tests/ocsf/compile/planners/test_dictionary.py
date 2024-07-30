from ocsf.repository import (
    Repository,
    DefinitionFile,
    DictionaryDefn,
    ObjectDefn,
    AttrDefn,
    ProfileDefn,
    IncludeDefn,
    CategoriesDefn,
)
from ocsf.compile.protoschema import ProtoSchema
from ocsf.compile.options import CompilationOptions
from ocsf.compile.planners.dictionary import DictionaryPlanner, DictionaryOp


def get_repo():
    repo = Repository()
    repo["dictionary.json"] = DefinitionFile(
        "dictionary.json",
        data=DictionaryDefn(
            caption="Dictionary",
            attributes={"a": AttrDefn(caption="A", type="string"), "b": AttrDefn(caption="B", type="string")},
        ),
    )
    repo["objects/databucket.json"] = DefinitionFile(
        "objects/databucket.json", data=ObjectDefn(attributes={"a": AttrDefn(description="A!")})
    )
    repo["profiles/data.json"] = DefinitionFile(
        "profiles/data.json", data=ProfileDefn(attributes={"b": AttrDefn(description="B!")})
    )
    repo["includes/thing.json"] = DefinitionFile(
        "includes/thing.json", data=IncludeDefn(attributes={"c": AttrDefn(caption="Thing")})
    )
    repo["categories.json"] = DefinitionFile("categories.json", data=CategoriesDefn())

    return repo


def get_schema():
    return ProtoSchema(get_repo())


def get_planner(ps: ProtoSchema):
    return DictionaryPlanner(ps, CompilationOptions())


def test_analyze_positive():
    ps = get_schema()
    planner = get_planner(ps)

    op = planner.analyze(ps["objects/databucket.json"])
    assert isinstance(op, DictionaryOp)
    assert op.target == "objects/databucket.json"
    assert op.prerequisite == "dictionary.json"


def test_analyze_negative():
    ps = get_schema()
    planner = get_planner(ps)

    op = planner.analyze(ps["categories.json"])
    assert op is None


def test_dictionary_op_apply():
    ps = get_schema()
    planner = get_planner(ps)
    op = planner.analyze(ps["objects/databucket.json"])

    assert isinstance(op, DictionaryOp)

    mr = op.apply(ps)
    assert len(mr) == 2
    assert ("attributes", "a", "caption") in mr
    assert ("attributes", "a", "type") in mr

    file = ps["objects/databucket.json"]
    d = file.data
    assert isinstance(d, ObjectDefn)
    assert d.caption is None
    assert isinstance(d.attributes, dict)
    assert "a" in d.attributes

    a = d.attributes["a"]
    assert isinstance(a, AttrDefn)
    assert a.caption == "A"
    assert a.description == "A!"
