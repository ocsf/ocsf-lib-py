import pytest

from ocsf.repository.definitions import DictionaryDefn, ProfileDefn, ObjectDefn, EventDefn, ExtensionDefn
from ocsf.repository.repository import DefinitionFile, Repository


def get_repo():
    r = Repository()
    r["dictionary.json"] = DefinitionFile("dictionary.json", data=DictionaryDefn())
    r["profiles/blue.json"] = DefinitionFile("profiles/blue.json", data=ProfileDefn(name="blue"))
    r["objects/base.json"] = DefinitionFile("objects/base.json", data=ObjectDefn(name="base"))
    r["events/base.json"] = DefinitionFile("events/base.json", data=EventDefn(name="base"))
    r["events/cat1/thing.json"] = DefinitionFile("events/cat1/thing.json", data=EventDefn(name="thing"))
    r["extensions/windows/extension.json"] = DefinitionFile(
        "extensions/windows/extension.json", data=ExtensionDefn(name="win")
    )
    r["extensions/linux/extension.json"] = DefinitionFile(
        "extensions/linux/extension.json", data=ExtensionDefn(name="linux")
    )
    r["extensions/linux/objects/process.json"] = DefinitionFile(
        "extensions/linux/objects/process.json", data=ObjectDefn(name="process")
    )
    r["extensions/windows/events/reg_key.json"] = DefinitionFile(
        "extensions/windows/events/reg_key.json", data=EventDefn(name="reg_key_activity")
    )
    r["extensions/windows/profiles/red.json"] = DefinitionFile(
        "extensions/windows/profiles/red.json", data=ProfileDefn(name="red")
    )

    return r


def test_basics():
    r = get_repo()

    assert len(r) == 10
    assert "dictionary.json" in r
    assert "profiles/blue.json" in r
    assert isinstance(r["objects/base.json"], DefinitionFile)
    del r["profiles/blue.json"]
    assert "profiles/blue.json" not in r


def test_files():
    r = get_repo()

    files = list(r.files())
    assert len(files) == 10
    assert all(isinstance(f, DefinitionFile) for f in files)


def test_paths():
    r = get_repo()

    paths = list(r.paths())
    assert len(paths) == 10
    assert all(isinstance(p, str) for p in paths)
    assert all(p == r[p].path for p in paths)


def test_profiles():
    r = get_repo()

    profiles = list(r.profiles())
    assert len(profiles) == 2
    assert "blue" in profiles
    assert "red" in profiles


def test_extensions():
    r = get_repo()

    extns = list(r.extensions())
    assert len(extns) == 2
    assert "windows" in extns
    assert "linux" in extns


def test_narrow():
    r = get_repo()

    narrowed = r.narrow("profiles/blue.json", ProfileDefn)
    assert isinstance(narrowed.data, ProfileDefn)

    with pytest.raises(TypeError):
        r.narrow("profiles/blue.json", ObjectDefn)
