from ocsf.compare import ChangedSchema, ChangedEvent, ChangedObject, ChangedAttr, Change
from ocsf.validate.compatibility import ChangedTypeFinding, NoChangedTypesRule


def test_changed_type_event():
    """Test that the rule finds a changed type in an event."""
    s = ChangedSchema(
        classes={
            "process_activity": ChangedEvent(
                attributes={
                    "process_name": ChangedAttr(type=Change("str_t", "process_name_t")),
                }
            ),
        }
    )

    rule = NoChangedTypesRule()
    findings = rule.validate(s)
    assert len(findings) == 1
    assert isinstance(findings[0], ChangedTypeFinding)


def test_changed_type_object():
    """Test that the rule finds a changed type in an object."""
    s = ChangedSchema(
        objects={
            "process_activity": ChangedObject(
                attributes={
                    "process_name": ChangedAttr(type=Change("str_t", "process_name_t")),
                }
            ),
        }
    )

    rule = NoChangedTypesRule()
    findings = rule.validate(s)
    assert len(findings) == 1
    assert isinstance(findings[0], ChangedTypeFinding)
