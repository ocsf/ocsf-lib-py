from ocsf.repository import (
    Repository,
    DictionaryDefn,
    DictionaryTypesDefn,
    DefinitionFile,
    ObjectDefn,
    TypeDefn,
    AttrDefn,
)
from ocsf.compile import CompilationOptions
from ocsf.compile.protoschema import ProtoSchema
from ocsf.compile.planners.observable import MarkObservablesPlanner, MarkObservablesOp
from ocsf.compile.planners.observable import _Registry # type: ignore


def get_ps():
    r = Repository()
    r["dictionary.json"] = DefinitionFile(
        "dictionary.json",
        data=DictionaryDefn(
            attributes={
                "attr1": AttrDefn(observable=1, caption="attr1"),
            },
            types=DictionaryTypesDefn(
                attributes={
                    "email_t": TypeDefn(observable=2, caption="email_t"),
                }
            ),
        ),
    )
    r["objects/thing.json"] = DefinitionFile(
        "objects/thing.json",
        data=ObjectDefn(
            attributes={
                "attr1": AttrDefn(caption="attr1"),
                "attr2": AttrDefn(caption="attr2", type="email_t"),
                "attr3": AttrDefn(caption="attr3"),
                "attr4": AttrDefn(caption="attr4", observable=3),
            }
        ),
    )

    return ProtoSchema(r)


def test_analyze():
    repo = get_ps()
    planner = MarkObservablesPlanner(repo, CompilationOptions(set_observable=True))
    analysis = planner.analyze(repo["objects/thing.json"])
    assert isinstance(analysis, list)
    assert len(analysis) == 1
    assert isinstance(analysis[0], MarkObservablesOp)
    assert analysis[0].target == "objects/thing.json"


def test_apply():
    schema = get_ps()
    reg = _Registry(schema)
    op = MarkObservablesOp(target="objects/thing.json", registry=reg)
    result = op.apply(schema)

    assert len(result) == 2
    assert ("attributes", "attr1", "observable") in result
    assert ("attributes", "attr2", "observable") in result
    data = schema["objects/thing.json"].data
    assert data is not None
    assert isinstance(data, ObjectDefn)
    assert data.attributes is not None
    assert "attr1" in data.attributes and isinstance(data.attributes["attr1"], AttrDefn)
    assert "attr2" in data.attributes and isinstance(data.attributes["attr2"], AttrDefn)
    assert "attr3" in data.attributes and isinstance(data.attributes["attr3"], AttrDefn)
    assert "attr4" in data.attributes and isinstance(data.attributes["attr4"], AttrDefn)
    assert data.attributes["attr1"].observable == 1
    assert data.attributes["attr2"].observable == 2
    assert data.attributes["attr3"].observable is None
    assert data.attributes["attr4"].observable == 3
