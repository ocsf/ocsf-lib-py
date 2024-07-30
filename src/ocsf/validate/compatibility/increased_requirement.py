"""A validation rule to identify changed attribute types."""

from dataclasses import dataclass
from ocsf.compare import ChangedSchema, Change, ChangedEvent, ChangedObject, ChangedAttr
from ocsf.schema import OcsfElementType
from ocsf.validate.framework import Rule, Finding, RuleMetadata


@dataclass
class IncreasedRequirementFinding(Finding):
    element_type: OcsfElementType
    path: tuple[str, str]
    before: str | None
    after: str

    def message(self) -> str:
        return (
            f"Requirement of {self.element_type.lower()} {'.'.join(self.path)} changed"
            + f" from {self.before} to {self.after}"
        )


_RULE_DESCRIPTION = """When the requirement of an attribute changes from
optional or recommended to required, previously valid records may no longer be
valid, breaking backwards compatibility. If you wish to increase the strength of
the requirement, you may change the requirement from optional to recommended
without breaking backwards compatibility."""


class NoIncreasedRequirementsRule(Rule[ChangedSchema]):
    def metadata(self):
        return RuleMetadata("No increased requirements", description=_RULE_DESCRIPTION)

    def validate(self, context: ChangedSchema) -> list[Finding]:
        findings: list[Finding] = []
        for name, event in context.classes.items():
            if isinstance(event, ChangedEvent):
                for attr_name, attr in event.attributes.items():
                    if isinstance(attr, ChangedAttr):
                        if isinstance(attr.requirement, Change) and attr.requirement.after == "required":
                            findings.append(
                                IncreasedRequirementFinding(
                                    OcsfElementType.EVENT,
                                    (name, attr_name),
                                    attr.requirement.before,
                                    attr.requirement.after,
                                )
                            )

        for name, obj in context.objects.items():
            if isinstance(obj, ChangedObject):
                for attr_name, attr in obj.attributes.items():
                    if isinstance(attr, ChangedAttr):
                        if isinstance(attr.requirement, Change) and attr.requirement.after == "required":
                            findings.append(
                                IncreasedRequirementFinding(
                                    OcsfElementType.OBJECT,
                                    (name, attr_name),
                                    attr.requirement.before,
                                    attr.requirement.after,
                                )
                            )

        return findings
