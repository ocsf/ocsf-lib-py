from ocsf.compare import Addition, ChangedAttr, ChangedEvent, ChangedObject, ChangedSchema, Removal
from ocsf.schema import OcsfAttr, OcsfEnumMember, OcsfEvent, OcsfObject
from ocsf.validate.compatibility.removed_records import (
    NoRemovedRecordsRule,
    RemovedAttrFinding,
    RemovedEnumMemberFinding,
    RemovedEventFinding,
    RemovedObjectFinding,
    RenamedAttrFinding,
    RenamedEnumMemberFinding,
    RenamedEventFinding,
    RenamedObjectFinding,
)

from .helpers import get_context


def test_removed_event():
    """Test that a RemovedEventFinding is created when an event is removed."""
    s = ChangedSchema()
    s.classes["email_delivery_activity"] = Removal(OcsfEvent("email_delivery_activity", "Email Delivery Activity"))

    rule = NoRemovedRecordsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], RemovedEventFinding)


def test_removed_object():
    """Test that a RemovedObjectFinding is created when an object is removed."""
    s = ChangedSchema()
    s.objects["kill_chain"] = Removal(OcsfObject("kill_chain", "Kill Chain"))

    rule = NoRemovedRecordsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], RemovedObjectFinding)


def test_removed_attr():
    """Test that a RemovedAttrFinding is created when an attribute is removed from an event or object."""
    s = ChangedSchema()
    s.classes["email_delivery_activity"] = ChangedEvent(
        attributes={"email_id": Removal(OcsfAttr("email_id", "Email ID", "required", "string_t"))}
    )
    s.objects["kill_chain"] = ChangedObject(
        attributes={"kill_chain_id": Removal(OcsfAttr("kill_chain_id", "Kill Chain ID", "required", "string_t"))}
    )

    rule = NoRemovedRecordsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 2
    assert isinstance(findings[0], RemovedAttrFinding)
    assert isinstance(findings[1], RemovedAttrFinding)


def test_removed_enum_member():
    """Test that a RemovedEnumMemberFinding is created when an enum member is removed from an attribute."""
    s = ChangedSchema()
    s.classes["email_delivery_activity"] = ChangedEvent(
        attributes={"email_status": ChangedAttr(enum={"1": Removal(OcsfEnumMember("sent", "Sent"))})}
    )
    s.objects["kill_chain"] = ChangedObject(
        attributes={"status": ChangedAttr(enum={"1": Removal(OcsfEnumMember("active", "Active"))})}
    )

    rule = NoRemovedRecordsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 2
    assert isinstance(findings[0], RemovedEnumMemberFinding)
    assert isinstance(findings[1], RemovedEnumMemberFinding)


def test_renamed_event_caption():
    """Test that a RenamedEventFinding is created when an event is renamed as identified by the caption."""
    s = ChangedSchema()
    s.classes["email_delivery_activity"] = Removal(
        OcsfEvent(name="email_delivery_activity", caption="Email Delivery Activity")
    )
    s.classes["email_delivery"] = Addition(OcsfEvent(name="email_delivery", caption="Email Delivery Activity"))

    rule = NoRemovedRecordsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], RenamedEventFinding)


def test_renamed_event_uid():
    """Test that a RenamedEventFinding is created when an event is renamed as identified by the class_uid."""
    uid: dict[str, OcsfEnumMember] = {"1020": OcsfEnumMember("Email Delivery Activity")}
    attrs: dict[str, OcsfAttr] = {"class_uid": OcsfAttr("class_uid", "Class UID", "required", "enum_t", enum=uid)}
    s = ChangedSchema()
    s.classes["email_delivery_activity"] = Removal(
        OcsfEvent(name="email_delivery_activity", caption="Email Delivery Activity", attributes=attrs)
    )
    s.classes["email_delivery"] = Addition(OcsfEvent(name="email_delivery", caption="Email Activity", attributes=attrs))

    rule = NoRemovedRecordsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], RenamedEventFinding)


def test_renamed_object():
    """Test that a RenamedObjectFinding is created when an object is renamed."""
    s = ChangedSchema()
    s.objects["kill_chain"] = Removal(OcsfObject(name="kill_chain", caption="Kill Chain"))
    s.objects["kill_chain_phases"] = Addition(OcsfObject(name="kill_chain_phases", caption="Kill Chain"))

    rule = NoRemovedRecordsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], RenamedObjectFinding)


def test_renamed_attr():
    """Test that a RenamedAttrFinding is created when an attribute is renamed."""
    s = ChangedSchema()
    s.classes["email_delivery_activity"] = ChangedEvent(
        attributes={
            "email_id": Removal(OcsfAttr("Email Address", "required", "string_t")),
            "email_address": Addition(OcsfAttr("Email Address", "required", "string_t")),
        }
    )

    rule = NoRemovedRecordsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], RenamedAttrFinding)


def test_renamed_enum_member():
    """Test that a RenamedEnumMemberFinding is created when an enum member is renamed."""
    s = ChangedSchema()
    s.classes["email_delivery_activity"] = ChangedEvent(
        attributes={
            "status": ChangedAttr(
                enum={
                    "1": Removal(OcsfEnumMember("sent")),
                    "2": Addition(OcsfEnumMember("sent")),
                }
            )
        }
    )

    rule = NoRemovedRecordsRule()
    findings = rule.validate(get_context(s))
    assert len(findings) == 1
    assert isinstance(findings[0], RenamedEnumMemberFinding)
