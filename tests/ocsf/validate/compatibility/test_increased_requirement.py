from ocsf.compare import ChangedSchema, ChangedEvent, ChangedObject, ChangedAttr, Change
from ocsf.validate.compatibility import IncreasedRequirementFinding, NoIncreasedRequirementsRule


def test_increased_requirement_event():
    """Test that the rule finds an increased requirement in an event."""
    s = ChangedSchema(
        classes={
            "process_activity": ChangedEvent(
                attributes={
                    "process_name": ChangedAttr(requirement=Change("recommended", "required")),
                }
            ),
        }
    )

    rule = NoIncreasedRequirementsRule()
    findings = rule.validate(s)
    assert len(findings) == 1
    assert isinstance(findings[0], IncreasedRequirementFinding)


def test_increased_requirement_object():
    """Test that the rule finds an increased requirement in an object."""
    s = ChangedSchema(
        objects={
            "process_activity": ChangedObject(
                attributes={
                    "process_name": ChangedAttr(requirement=Change("recommended", "required")),
                }
            ),
        }
    )

    rule = NoIncreasedRequirementsRule()
    findings = rule.validate(s)
    assert len(findings) == 1
    assert isinstance(findings[0], IncreasedRequirementFinding)


def test_increased_requirement_event_bugfix():
    """Test that the rule allows 'bugfix' increases to requirements for key attributes defined on base_event."""
    s = ChangedSchema(
        classes={
            "process_activity": ChangedEvent(
                attributes={
                    "activity_id": ChangedAttr(requirement=Change("recommended", "required")),
                }
            ),
        }
    )

    rule = NoIncreasedRequirementsRule()
    findings = rule.validate(s)
    assert len(findings) == 0
