import pytest

from ocsf.repository.helpers import path_defn_t, RepoPaths, SpecialFiles, REPO_PATHS, SPECIAL_FILES
from ocsf.repository.definitions import (
    ObjectDefn,
    EventDefn,
    IncludeDefn,
    ProfileDefn,
    DictionaryDefn,
    CategoriesDefn,
    VersionDefn,
    ExtensionDefn,
)


def test_path_defn_t():
    assert path_defn_t(RepoPaths.OBJECTS.value, "foo.json") is ObjectDefn
    assert path_defn_t(RepoPaths.EVENTS.value, "foo.json") is EventDefn
    assert path_defn_t(RepoPaths.EVENTS.value, "some_cat", "foo.json") is EventDefn
    assert path_defn_t(RepoPaths.INCLUDES.value, "foo.json") is IncludeDefn
    assert path_defn_t(RepoPaths.INCLUDES.value, "some_dir", "foo.json") is IncludeDefn
    assert path_defn_t(RepoPaths.PROFILES.value, "foo.json") is ProfileDefn
    assert path_defn_t(RepoPaths.PROFILES.value, "some_dir", "foo.json") is ProfileDefn
    assert path_defn_t(SpecialFiles.DICTIONARY.value) is DictionaryDefn
    assert path_defn_t(SpecialFiles.CATEGORIES.value) is CategoriesDefn
    assert path_defn_t(SpecialFiles.VERSION.value) is VersionDefn

    assert path_defn_t(RepoPaths.EXTENSIONS.value, "extn", RepoPaths.OBJECTS.value, "foo.json") is ObjectDefn
    assert path_defn_t(RepoPaths.EXTENSIONS.value, "extn", RepoPaths.EVENTS.value, "foo.json") is EventDefn
    assert path_defn_t(RepoPaths.EXTENSIONS.value, "extn", RepoPaths.EVENTS.value, "some_cat", "foo.json") is EventDefn
    assert path_defn_t(RepoPaths.EXTENSIONS.value, "extn", RepoPaths.INCLUDES.value, "foo.json") is IncludeDefn
    assert (
        path_defn_t(RepoPaths.EXTENSIONS.value, "extn", RepoPaths.INCLUDES.value, "some_dir", "foo.json") is IncludeDefn
    )
    assert path_defn_t(RepoPaths.EXTENSIONS.value, "extn", RepoPaths.PROFILES.value, "foo.json") is ProfileDefn
    assert (
        path_defn_t(RepoPaths.EXTENSIONS.value, "extn", RepoPaths.PROFILES.value, "some_dir", "foo.json") is ProfileDefn
    )
    assert path_defn_t(RepoPaths.EXTENSIONS.value, "extn", SpecialFiles.DICTIONARY.value) is DictionaryDefn
    assert path_defn_t(RepoPaths.EXTENSIONS.value, "extn", SpecialFiles.CATEGORIES.value) is CategoriesDefn
    assert path_defn_t(RepoPaths.EXTENSIONS.value, "extn", SpecialFiles.EXTENSION.value) is ExtensionDefn

    with pytest.raises(ValueError):
        print(path_defn_t("foo.json"))
    with pytest.raises(ValueError):
        print(path_defn_t("objects/"))
    with pytest.raises(ValueError):
        path_defn_t("extensions/events/foo.json")
    with pytest.raises(ValueError):
        path_defn_t("extensions/extn/foo.json")


def test_repo_path_tuple_values():
    """Verify that the REPO_PATHS tuple contains the same values as the RepoPaths enum."""
    enum_paths = [x.value for x in RepoPaths]
    for rp in REPO_PATHS:
        assert rp in enum_paths, f"REPO_PATH tuple contains `{rp}` which is not in the RepoPaths Enum"

    for e in RepoPaths:
        assert e.value in REPO_PATHS, f"REPO_PATH tuple is missing `{e.value}`"


def test_special_files_tuple_values():
    """Verify that the REPO_PATHS tuple contains the same values as the RepoPaths enum."""
    enum_paths = [x.value for x in SpecialFiles]
    for rp in SPECIAL_FILES:
        assert rp in enum_paths, f"SPECIAL_FILES tuple contains `{rp}` which is not in the SpecialFiles Enum"

    for e in SpecialFiles:
        assert e.value in SPECIAL_FILES, f"SPECIAL_FILES tuple is missing `{e.value}`"
