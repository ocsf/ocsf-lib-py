from ocsf.repository import Repository, DefinitionFile, ProfileDefn, AttrDefn, ExtensionDefn
from ocsf.compile.protoschema import ProtoSchema
from ocsf.compile.planners.profile import (
    #ExcludeProfileAttrsOp,
    #MarkProfileOp,
    #MarkProfilePlanner,
    #ExcludeProfileAttrsPlanner,
    _find_profile, #type: ignore
)


def get_repo():
    repo = Repository()
    repo["profiles/prof.json"] = DefinitionFile(
        "profiles/prof.json", data=ProfileDefn(attributes={"a": AttrDefn(description="A!")})
    )
    repo["profiles/network.json"] = DefinitionFile(
        "profiles/network.json", data=ProfileDefn(attributes={"b": AttrDefn(description="B!")})
    )
    repo["extensions/linux/profiles/linux_user.json"] = DefinitionFile(
        "extensions/linux/profiles/linux_user.json",
        data=ProfileDefn(attributes={"d": AttrDefn(description="D!")}),
    )
    repo["extensions/windows/profiles/ldap_stuff.json"] = DefinitionFile(
        "extensions/windows/profiles/ldap_stuff.json",
        data=ProfileDefn(attributes={"d": AttrDefn(description="D!")}),
    )
    repo["extensions/linux/extension.json"] = DefinitionFile(
        "extensions/linux/extension.json", data=ExtensionDefn(name="linux", uid=1)
    )
    repo["extensions/windows/extension.json"] = DefinitionFile(
        "extensions/windows/extension.json", data=ExtensionDefn(name="win", uid=2)
    )

    return repo


def get_schema():
    return ProtoSchema(get_repo())


def test_find_profile():
    assert _find_profile(get_schema(), "prof", "events/iam/account_change.json") == "profiles/prof.json"
    assert (
        _find_profile(get_schema(), "win/ldap_stuff", "events/iam/account_change.json")
        == "extensions/windows/profiles/ldap_stuff.json"
    )
