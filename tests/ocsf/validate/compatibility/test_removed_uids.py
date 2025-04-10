from ocsf.compare import Addition, ChangedAttr, ChangedEvent, ChangedSchema, Removal
from ocsf.schema import OcsfEnumMember
from ocsf.validate.compatibility import ChangedClassUidFinding, NoChangedClassUidsRule

from .helpers import get_context


def test_changed_class_uid():
    """Test that the rule finds a changed class UID."""
    s = ChangedSchema(
        classes={
            "process_activity": ChangedEvent(
                attributes={
                    "class_uid": ChangedAttr(
                        enum={
                            "123": Removal(OcsfEnumMember("Process Activity")),
                            "456": Addition(OcsfEnumMember("Process Activity")),
                        }
                    ),
                }
            ),
        }
    )

    rule = NoChangedClassUidsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], ChangedClassUidFinding)
    assert findings[0].event == "process_activity"
    assert findings[0].before == "123"
    assert findings[0].after == "456"
