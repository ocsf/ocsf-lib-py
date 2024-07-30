from ocsf.repository import (
    Repository,
    DefinitionFile,
    AttrDefn,
    EventDefn,
    CategoriesDefn,
    CategoryDefn,
    ExtensionDefn,
    EnumMemberDefn,
)
from ocsf.compile.protoschema import ProtoSchema
from ocsf.compile.options import CompilationOptions
from ocsf.compile.planners.uid import UidPlanner, UidOp


def get_repo():
    repo = Repository()
    repo["categories.json"] = DefinitionFile(
        "categories.json",
        data=CategoriesDefn(
            attributes={"network": CategoryDefn(uid=1, caption="Network Cat", description="Network Cat Desc")}
        ),
    )
    repo["events/network/network.json"] = DefinitionFile(
        "events/network/network.json",
        data=EventDefn(
            uid=2,
            category="network",
            caption="Network",
            description="Network Desc",
            attributes={
                "b": AttrDefn(description="B!"),
                "activity_id": AttrDefn(enum={"1": EnumMemberDefn(caption="One"), "2": EnumMemberDefn(caption="Two")}),
            },
        ),
    )
    repo["extensions/win/events/network/cifs_activity.json"] = DefinitionFile(
        "extensions/win/events/network/cifs_activity.json",
        data=EventDefn(
            uid=3,
            category="network",
            caption="CIFS",
            description="CIFS Desc",
            src_extension="win",
            attributes={
                "d": AttrDefn(description="D!"),
                "activity_id": AttrDefn(enum={"1": EnumMemberDefn(caption="One"), "2": EnumMemberDefn(caption="Two")}),
            },
        ),
    )
    repo["extensions/win/extension.json"] = DefinitionFile("extensions/win/extension.json", data=ExtensionDefn(uid=4))

    return repo


def get_schema():
    return ProtoSchema(get_repo())


def get_planner(ps: ProtoSchema):
    return UidPlanner(ps, CompilationOptions())


def test_analyze():
    ps = get_schema()
    planner = get_planner(ps)

    op = planner.analyze(ps["events/network/network.json"])
    assert isinstance(op, UidOp)
    assert op.target == "events/network/network.json"
    assert op.prerequisite == "categories.json"

    op = planner.analyze(ps["extensions/win/events/network/cifs_activity.json"])
    assert isinstance(op, UidOp)
    assert op.target == "extensions/win/events/network/cifs_activity.json"
    assert op.prerequisite == "categories.json"

    op = planner.analyze(ps["extensions/win/extension.json"])
    assert op is None


def test_apply():
    ps = get_schema()
    op = UidOp("events/network/network.json", "categories.json")

    r = op.apply(ps)

    assert ("attributes", "category_uid") in r
    assert ("attributes", "class_uid") in r
    assert ("attributes", "type_uid") in r
    assert ("uid",) in r
    event = ps["events/network/network.json"].data
    assert isinstance(event, EventDefn)
    assert event.attributes is not None

    # Verify category_uid
    assert "category_uid" in event.attributes
    assert isinstance(event.attributes["category_uid"], AttrDefn)
    assert event.attributes["category_uid"].enum is not None
    assert "1" in event.attributes["category_uid"].enum
    assert len(event.attributes["category_uid"].enum) == 1
    assert event.attributes["category_uid"].enum["1"].caption == "Network Cat"
    assert event.attributes["category_uid"].enum["1"].description == "Network Cat Desc"

    # Verify class_uid
    assert "class_uid" in event.attributes
    assert isinstance(event.attributes["class_uid"], AttrDefn)
    assert event.attributes["class_uid"].enum is not None
    assert "1002" in event.attributes["class_uid"].enum
    assert len(event.attributes["class_uid"].enum) == 1
    assert event.attributes["class_uid"].enum["1002"].caption == "Network"
    assert event.attributes["class_uid"].enum["1002"].description == "Network Desc"

    # Verify type_uid
    assert "type_uid" in event.attributes
    assert isinstance(event.attributes["type_uid"], AttrDefn)
    assert event.attributes["type_uid"].enum is not None
    assert "100201" in event.attributes["type_uid"].enum
    assert "100202" in event.attributes["type_uid"].enum
    assert len(event.attributes["type_uid"].enum) == 2
    assert event.attributes["type_uid"].enum["100201"].caption == "Network: One"
    assert event.attributes["type_uid"].enum["100202"].caption == "Network: Two"


def test_apply_extn():
    ps = get_schema()
    op = UidOp("extensions/win/events/network/cifs_activity.json", "categories.json")

    r = op.apply(ps)

    assert ("attributes", "category_uid") in r
    assert ("attributes", "class_uid") in r
    assert ("attributes", "type_uid") in r
    assert ("uid",) in r
    event = ps["extensions/win/events/network/cifs_activity.json"].data
    assert isinstance(event, EventDefn)
    assert event.attributes is not None

    # Verify category_uid
    assert "category_uid" in event.attributes
    assert isinstance(event.attributes["category_uid"], AttrDefn)
    assert event.attributes["category_uid"].enum is not None
    assert "1" in event.attributes["category_uid"].enum
    assert len(event.attributes["category_uid"].enum) == 1
    assert event.attributes["category_uid"].enum["1"].caption == "Network Cat"
    assert event.attributes["category_uid"].enum["1"].description == "Network Cat Desc"

    # Verify class_uid
    assert "class_uid" in event.attributes
    assert isinstance(event.attributes["class_uid"], AttrDefn)
    assert event.attributes["class_uid"].enum is not None
    assert "401003" in event.attributes["class_uid"].enum
    assert len(event.attributes["class_uid"].enum) == 1
    assert event.attributes["class_uid"].enum["401003"].caption == "CIFS"
    assert event.attributes["class_uid"].enum["401003"].description == "CIFS Desc"

    # Verify type_uid
    assert "type_uid" in event.attributes
    assert isinstance(event.attributes["type_uid"], AttrDefn)
    assert event.attributes["type_uid"].enum is not None
    assert "40100301" in event.attributes["type_uid"].enum
    assert "40100302" in event.attributes["type_uid"].enum
    assert len(event.attributes["type_uid"].enum) == 2
    assert event.attributes["type_uid"].enum["40100301"].caption == "CIFS: One"
    assert event.attributes["type_uid"].enum["40100302"].caption == "CIFS: Two"
