from ocsf.compare import Change, ChangedAttr, ChangedEvent, ChangedObject, ChangedSchema
from ocsf.validate.compatibility import ChangedTypeFinding, NoChangedTypesRule
from .helpers import get_context


def test_changed_type_event():
    """Test that the rule finds a changed type in an event."""
    s = ChangedSchema(
        classes={
            "process_activity": ChangedEvent(
                attributes={
                    "process_name": ChangedAttr(type=Change("string_t", "long_t")),
                }
            ),
        }
    )

    rule = NoChangedTypesRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], ChangedTypeFinding)


def test_changed_type_object():
    """Test that the rule finds a changed type in an object."""
    s = ChangedSchema(
        objects={
            "process_activity": ChangedObject(
                attributes={
                    "process_name": ChangedAttr(type=Change("string_t", "long_t")),
                }
            ),
        }
    )

    rule = NoChangedTypesRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], ChangedTypeFinding)


def test_int_to_long():
    """Test that changing an int to a long is allowed."""
    s = ChangedSchema(
        objects={
            "process_activity": ChangedObject(
                attributes={
                    "process_name": ChangedAttr(type=Change("integer_t", "long_t")),
                }
            ),
        },
        classes={
            "process_activity": ChangedEvent(
                attributes={
                    "process_name": ChangedAttr(type=Change("integer_t", "long_t")),
                }
            ),
        },
    )
    rule = NoChangedTypesRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 0


def test_str_to_filepath():
    """Test that changing from string_t to file_path_t is allowed."""
    s = ChangedSchema(
        objects={
            "process_activity": ChangedObject(
                attributes={
                    "process_name": ChangedAttr(type=Change("string_t", "file_path_t")),
                }
            ),
        },
        classes={
            "process_activity": ChangedEvent(
                attributes={
                    "process_name": ChangedAttr(type=Change("string_t", "file_path_t")),
                }
            ),
        },
    )
    rule = NoChangedTypesRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 0
