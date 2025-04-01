from ocsf.compare import Addition, ChangedEvent, ChangedObject, ChangedSchema
from ocsf.schema import OcsfAttr, OcsfProfile
from ocsf.validate.compatibility.added_required_attrs import AddedRequiredAttrFinding, NoAddedRequiredAttrsRule
from ocsf.validate.framework import Severity

from .helpers import get_context


def test_added_required_attr_event():
    """Test that the rule finds an added required attribute in an event."""
    s = ChangedSchema(
        classes={
            "process_activity": ChangedEvent(
                attributes={
                    "process_name": Addition(OcsfAttr(caption="", type="str_t", requirement="required")),
                }
            ),
        }
    )

    rule = NoAddedRequiredAttrsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], AddedRequiredAttrFinding)
    assert findings[0].severity == Severity.WARNING


def test_added_required_attr_object():
    """Test that the rule finds an added required attribute in an object."""
    s = ChangedSchema(
        objects={
            "process": ChangedObject(
                attributes={
                    "process_name": Addition(OcsfAttr(caption="", type="str_t", requirement="required")),
                }
            ),
        }
    )

    rule = NoAddedRequiredAttrsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], AddedRequiredAttrFinding)
    assert findings[0].severity == Severity.WARNING


def test_added_required_attr_profile():
    """Test that the rule does not find an added required attribute in a profile."""
    s = ChangedSchema(
        classes={
            "process_activity": ChangedEvent(
                attributes={
                    "process_name": Addition(OcsfAttr(caption="", type="str_t", requirement="required")),
                }
            ),
        },
        profiles={
            "profile": Addition(
                after=OcsfProfile(
                    caption="profile",
                    name="profile",
                    attributes={
                        "process_name": OcsfAttr(caption="", type="str_t", requirement="required"),
                    },
                )
            ),
        },
    )

    rule = NoAddedRequiredAttrsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 0

    s.classes["file_activity"] = ChangedEvent(
        attributes={
            "file_name": Addition(OcsfAttr(caption="", type="str_t", requirement="required")),
        }
    )
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], AddedRequiredAttrFinding)
    assert findings[0].severity == Severity.ERROR
