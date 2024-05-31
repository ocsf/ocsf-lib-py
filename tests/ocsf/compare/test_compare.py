# pyright: reportPrivateUsage = false
from typing import Optional, Any

from ocsf.compare import (
    compare,
    compare_dict,
    Change,
    NoChange,
    ChangedAttr,
    ChangedEnumMember,
    Removal,
    Addition,
)
from ocsf.schema import OcsfAttr, OcsfEnumMember


def test_compare_primitives():
    """Test compare() on primitive arguments (int, bool, list[int], Optional[_], etc.)."""

    assert compare(1, 2) == Change(before=1, after=2)
    assert compare(True, False) == Change(before=True, after=False)
    assert compare(True, True) == NoChange[bool]()
    assert compare([1, 2, 3], [1, 2]) == Change(before=[1, 2, 3], after=[1, 2])
    assert compare("test1", "test2") == Change(before="test1", after="test2")

    x1: Optional[bool] = True
    x2: Optional[bool] = None
    assert compare(x1, x2) == Change(True, None)


def test_compare_scalar_properties():
    """Test compare() on scalar properties of an OcsfModel."""

    old_attr = OcsfAttr(caption="test1", description="", requirement="required", type="int_t")
    new_attr = OcsfAttr(caption="test2", description="", requirement="required", type="int_t")
    diff = compare(old_attr, new_attr)

    assert isinstance(diff, ChangedAttr)
    assert diff.caption == Change(before="test1", after="test2")
    assert diff.description == NoChange()
    assert diff.requirement == NoChange()
    assert diff.enum == NoChange()  # {}


def test_compare_optional_property():
    """Test compare() on an optional property changing to and from None."""

    old_attr = OcsfAttr(caption="test1", group=None, description="", requirement="required", type="int_t")
    new_attr = OcsfAttr(caption="test2", group="test", description="", requirement="required", type="int_t")
    diff = compare(old_attr, new_attr)

    assert isinstance(diff, ChangedAttr)
    assert diff.group == Change(before=None, after="test")

    diff = compare(new_attr, old_attr)

    assert isinstance(diff, ChangedAttr)
    assert diff.group == Change(after=None, before="test")


def test_compare_optional_dict_property():
    """Test compare() on a property of type Optional[dict[_, _]] like OcsfAttr.enum."""

    old_attr = OcsfAttr(
        caption="test",
        description="",
        requirement="required",
        type="int_t",
        enum={
            "1": OcsfEnumMember(caption="Other"),
            "-1": OcsfEnumMember(caption="Unknown"),
        },
    )
    new_attr = OcsfAttr(
        caption="test",
        description="",
        requirement="required",
        type="int_t",
        enum={
            "1": OcsfEnumMember(caption="Other"),
            "99": OcsfEnumMember(caption="Unknown"),
        },
    )

    diff = compare(old_attr, new_attr)
    assert isinstance(diff, ChangedAttr)
    assert diff.caption == NoChange()

    assert isinstance(diff.enum, dict)
    assert "1" in diff.enum
    assert "-1" in diff.enum
    assert "99" in diff.enum
    assert diff.enum["-1"] == Removal(before=OcsfEnumMember(caption="Unknown"))
    assert diff.enum["1"] == NoChange()
    assert diff.enum["99"] == Addition(after=OcsfEnumMember(caption="Unknown"))


def test_compare_dict_two_dicts():
    """Test compare_dict() on two dictionaries with different keys and values."""

    d1: dict[int, str] = {1: "a", 2: "b", 3: "c"}
    d2: dict[int, str] = {0: "a", 2: "b", 3: "d"}

    diff = compare_dict(d1, d2)
    assert isinstance(diff, dict)

    for i in (0, 1, 2, 3):
        assert i in diff

    assert diff[0] == Addition(after="a")
    assert diff[1] == Removal(before="a")
    assert diff[2] == NoChange()
    assert diff[3] == Change(before="c", after="d")


def test_compare_dict_two_null():
    """Test compare_dict() on two None values."""

    diff: Any = compare_dict(None, None)
    assert isinstance(diff, NoChange)


def test_compare_dict_one_dict():
    """Test compare_dict() on one dictionary and one None value."""

    d1: dict[int, str] = {1: "a", 2: "b", 3: "c"}

    diff = compare_dict(d1, None)
    assert isinstance(diff, dict)

    for i in (1, 2, 3):
        assert i in diff

    assert diff[1] == Removal(before="a")
    assert diff[2] == Removal(before="b")
    assert diff[3] == Removal(before="c")

    diff = compare_dict(None, d1)
    assert isinstance(diff, dict)

    for i in (1, 2, 3):
        assert i in diff

    assert diff[1] == Addition(after="a")
    assert diff[2] == Addition(after="b")
    assert diff[3] == Addition(after="c")


def test_compare_dict_ocsf_models():
    """Test compare_dict() on two dictionaries with OcsfModel values."""

    e1 = {
        "1": OcsfEnumMember(caption="Other"),
        "2": OcsfEnumMember(caption="Success"),
        "3": OcsfEnumMember(caption="Failure"),
        "4": OcsfEnumMember(caption="Unknown"),
    }
    e2 = {
        "2": OcsfEnumMember(caption="Winning!"),
        "3": OcsfEnumMember(caption="Failure"),
        "4": OcsfEnumMember(caption="Unknown"),
        "5": OcsfEnumMember(caption="Flattened"),
    }

    diff = compare_dict(e1, e2)
    assert isinstance(diff, dict)
    assert diff["1"] == Removal(before=OcsfEnumMember(caption="Other"))
    assert diff["2"] == ChangedEnumMember(caption=Change(before="Success", after="Winning!"))
    assert diff["3"] == NoChange()
    assert diff["4"] == NoChange()
    assert diff["5"] == Addition(after=OcsfEnumMember(caption="Flattened"))
