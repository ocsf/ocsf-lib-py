"""A validation rule to identify changed attribute types."""

from dataclasses import dataclass

from ocsf.compare import Change, ChangedAttr, ChangedEvent, ChangedObject
from ocsf.schema import OcsfElementType
from ocsf.validate.framework import Finding, Rule, RuleMetadata

from .context import CompatibilityContext


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

_ALLOWED = ["category_uid", "activity_id", "class_uid"]


class NoIncreasedRequirementsRule(Rule[CompatibilityContext]):
    def metadata(self):
        return RuleMetadata("No increased requirements", description=_RULE_DESCRIPTION)

    def validate(self, context: CompatibilityContext) -> list[Finding]:
        findings: list[Finding] = []
        for name, event in context.change.classes.items():
            if isinstance(event, ChangedEvent):
                for attr_name, attr in event.attributes.items():
                    if isinstance(attr, ChangedAttr):
                        if (
                            isinstance(attr.requirement, Change)
                            and attr.requirement.after == "required"
                            and attr_name not in _ALLOWED
                        ):
                            findings.append(
                                IncreasedRequirementFinding(
                                    OcsfElementType.EVENT,
                                    (name, attr_name),
                                    attr.requirement.before,
                                    attr.requirement.after,
                                )
                            )

        for name, obj in context.change.objects.items():
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
