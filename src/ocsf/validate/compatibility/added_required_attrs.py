"""A validation rule to identify changed attribute types."""

from dataclasses import dataclass
from ocsf.compare import ChangedSchema, ChangedEvent, ChangedObject, Addition
from ocsf.schema import OcsfElementType
from ocsf.validate.framework import Rule, Finding, RuleMetadata
from ocsf.validate.framework.validator import Severity


@dataclass
class AddedRequiredAttrFinding(Finding):
    element_type: OcsfElementType
    path: tuple[str, str]

    def message(self) -> str:
        return "New required attribute added to " + f"{self.element_type.lower()} {'.'.join(self.path)}"


_RULE_DESCRIPTION = """When a required attribute is added to an existing object
or event, records produced using an older schema will not contain the new
attribute and will be invalid. If you are adding an attribute to an existing
event or object, it should be optional or recommended. Note: required attributes
can be added in new profiles, because older records won't have been produced
using the new profile."""


def attr_in_added_profile(attr_name: str, context: ChangedSchema) -> bool:
    for _, profile in context.profiles.items():
        if isinstance(profile, Addition):
            if attr_name in profile.after.attributes:
                return True
    return False


class NoAddedRequiredAttrsRule(Rule[ChangedSchema]):
    def metadata(self):
        return RuleMetadata("No added required attributes", description=_RULE_DESCRIPTION)

    def validate(self, context: ChangedSchema) -> list[Finding]:
        findings: list[Finding] = []

        for name, event in context.classes.items():
            if isinstance(event, ChangedEvent):
                for attr_name, attr in event.attributes.items():
                    if isinstance(attr, Addition):
                        if attr.after.requirement == "required" and not attr_in_added_profile(attr_name, context):
                            findings.append(AddedRequiredAttrFinding(OcsfElementType.EVENT, (name, attr_name)))

        for name, obj in context.objects.items():
            if isinstance(obj, ChangedObject):
                for attr_name, attr in obj.attributes.items():
                    if isinstance(attr, Addition):
                        if attr.after.requirement == "required" and not attr_in_added_profile(attr_name, context):
                            findings.append(AddedRequiredAttrFinding(OcsfElementType.OBJECT, (name, attr_name)))

        # If there are no profiles, downgrade all findings to warnings because we can't be sure they
        # weren't added in a new profile.
        if len(context.profiles) == 0:
            for finding in findings:
                finding.set_severity(Severity.WARNING)

        return findings
