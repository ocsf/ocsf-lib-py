from dataclasses import dataclass
from typing import Optional

from ocsf.compile.merge import MergeOptions, merge
from ocsf.repository import DefinitionPart


def test_options_init():
    o = MergeOptions()
    assert o.overwrite is None
    assert o.allowed_fields is None
    assert o.ignored_fields is None


@dataclass
class LeftPart(DefinitionPart):
    in_both: Optional[int] = None
    in_left: Optional[int] = None


@dataclass
class RightPart(DefinitionPart):
    in_both: Optional[int] = None
    in_right: Optional[int] = None


def test_basic_merge():
    left = LeftPart(in_both=1, in_left=2)
    right = RightPart(in_both=2, in_right=3)
    r = merge(left, right)
    assert left.in_both == 1
    assert left.in_left == 2
    assert not hasattr(left, "in_right")
    assert len(r) == 0

    left = LeftPart(in_both=None, in_left=2)
    right = RightPart(in_both=2, in_right=3)
    r = merge(left, right)
    assert left.in_both == 2
    assert len(r) == 1
    assert r[0] == ("in_both",)


def test_overwrite_merge():
    left = LeftPart(in_both=1, in_left=2)
    right = RightPart(in_both=2, in_right=3)
    r = merge(left, right, overwrite=True)
    assert left.in_both == 2
    assert len(r) == 1
    assert r[0] == ("in_both",)


@dataclass
class SimplePart(DefinitionPart):
    value: Optional[int] = None


@dataclass
class ComplexPart(DefinitionPart):
    value: Optional[int] = None
    other: Optional[SimplePart] = None
    attrs: Optional[dict[str, SimplePart | str | list[str]]] = None


def complex_setup():
    left = ComplexPart(
        value=1,
        other=SimplePart(value=2),
        attrs={"a": SimplePart(value=3), "b": SimplePart(value=4), "d": SimplePart(value=None)},
    )
    right = ComplexPart(
        value=2,
        other=SimplePart(value=3),
        attrs={"a": SimplePart(value=4), "c": SimplePart(value=5), "d": SimplePart(value=6)},
    )
    return left, right


def test_complex_merge():
    left, right = complex_setup()
    r = merge(left, right)
    assert left.value == 1
    assert left.other is not None
    assert left.other.value == 2
    assert left.attrs is not None
    assert isinstance(left.attrs["a"], SimplePart)
    assert left.attrs["a"].value == 3
    assert isinstance(left.attrs["b"], SimplePart)
    assert left.attrs["b"].value == 4
    assert isinstance(left.attrs["c"], SimplePart)
    assert left.attrs["c"].value == 5
    assert isinstance(left.attrs["d"], SimplePart)
    assert left.attrs["d"].value == 6
    assert len(r) == 2
    assert ("attrs", "c") in r
    assert ("attrs", "d", "value") in r

    left.other.value = None
    r = merge(left, right)
    assert left.other.value == 3


def test_attrs_merge():
    left, right = complex_setup()
    right.attrs = {
        "include_": "somefile.json",
        "a": SimplePart(value=4),
        "c": SimplePart(value=5),
        "d": SimplePart(value=6),
    }
    r = merge(left, right)

    assert left.value == 1
    assert left.other is not None
    assert left.other.value == 2
    assert left.attrs is not None
    assert isinstance(left.attrs["a"], SimplePart)
    assert left.attrs["a"].value == 3
    assert isinstance(left.attrs["b"], SimplePart)
    assert left.attrs["b"].value == 4
    assert isinstance(left.attrs["c"], SimplePart)
    assert left.attrs["c"].value == 5
    assert isinstance(left.attrs["d"], SimplePart)
    assert left.attrs["d"].value == 6
    assert len(r) == 3
    assert ("attrs", "c") in r
    assert ("attrs", "d", "value") in r


def test_allowed_fields():
    left, right = complex_setup()
    r = merge(left, right, overwrite=True, allowed_fields=[("value",), ("other", "value")])
    assert left.value == 2
    assert left.other is not None
    assert left.other.value == 3
    assert left.attrs is not None
    assert "c" not in left.attrs
    assert len(r) == 2
    assert ("value",) in r
    assert ("other", "value") in r


def test_allowed_fields_string():
    left, right = complex_setup()
    r = merge(left, right, overwrite=True, allowed_fields=["value", "other"])
    assert left.value == 2
    assert left.other is not None
    assert left.other.value == 3
    assert left.attrs is not None
    assert "c" not in left.attrs
    assert len(r) == 2
    assert ("value",) in r
    assert ("other", "value") in r


def test_ignored_fields():
    left, right = complex_setup()
    r = merge(left, right, ignored_fields=[("attrs", "a")])
    assert left.value == 1
    assert left.other is not None
    assert left.other.value == 2
    assert left.attrs is not None
    assert "a" in left.attrs and isinstance(left.attrs["a"], SimplePart)
    assert left.attrs["a"].value == 3
    assert "b" in left.attrs and isinstance(left.attrs["b"], SimplePart)
    assert left.attrs["b"].value == 4
    assert "c" in left.attrs and isinstance(left.attrs["c"], SimplePart)
    assert left.attrs["c"].value == 5
    assert len(r) == 2
    assert ("attrs", "c") in r


def test_empty_left_dict():
    left = ComplexPart(
        value=1,
        other=SimplePart(value=2),
        attrs=None,
    )
    right = ComplexPart(
        value=2,
        other=SimplePart(value=3),
        attrs={"a": SimplePart(value=4), "c": SimplePart(value=5), "d": SimplePart(value=6)},
    )
    r = merge(left, right)
    assert len(r) == 1
    assert left.attrs is not None
    assert "a" in left.attrs

    left.attrs = {}
    r = merge(left, right)
    assert len(r) == 3
    assert left.attrs is not None
    assert "a" in left.attrs
