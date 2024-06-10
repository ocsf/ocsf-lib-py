from ocsf.schema import (
    OcsfSchema,
    OcsfEvent,
    OcsfObject,
    OcsfAttr,
    OcsfDeprecationInfo,
    OcsfType,
    OcsfVersion,
    OcsfEnumMember,
)
from ocsf.compare.model import (
    ChangedSchema,
    ChangedEvent,
    ChangedObject,
    ChangedAttr,
    ChangedDeprecationInfo,
    ChangedType,
    ChangedVersion,
    ChangedEnumMember,
)
from ocsf.compare.factory import create_diff


def test_create_diff():
    """Test that the factory creates the correct diff model for each OCSF model."""
    mapping = {
        ChangedSchema: OcsfSchema(version="1.0.0"),
        ChangedEvent: OcsfEvent(caption="", name=""),
        ChangedObject: OcsfObject(caption="", name=""),
        ChangedAttr: OcsfAttr(caption="", requirement="required", type="string_t"),
        ChangedDeprecationInfo: OcsfDeprecationInfo(since="1.0.0", message=""),
        ChangedType: OcsfType(caption=""),
        ChangedVersion: OcsfVersion(version="1.0.0"),
        ChangedEnumMember: OcsfEnumMember(caption=""),
    }

    for changed_t, ocsf_model in mapping.items():
        assert create_diff(ocsf_model) == changed_t()
