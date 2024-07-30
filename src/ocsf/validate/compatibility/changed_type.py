"""A validation rule to identify changed attribute types."""

from dataclasses import dataclass
from ocsf.compare import ChangedSchema, Change, ChangedEvent, ChangedObject, ChangedAttr
from ocsf.schema import OcsfElementType
from ocsf.validate.framework import Rule, Finding, RuleMetadata


@dataclass
class ChangedTypeFinding(Finding):
    element_type: OcsfElementType
    record: str
    attr: str
    before: str | None
    after: str | None

    def message(self) -> str:
        return (
            f"Type of {self.element_type.lower()} {self.record}.{self.attr} "
            + f"changed from {self.before} to {self.after}"
        )


_RULE_DESCRIPTION = """Changing the type of an attribute can break backwards
compatibility in some encodings, so any change to an attribute's data type is
considered breaking."""


class NoChangedTypesRule(Rule[ChangedSchema]):
    def metadata(self):
        return RuleMetadata("No changed attribute types", description=_RULE_DESCRIPTION)

    def validate(self, context: ChangedSchema) -> list[Finding]:
        findings: list[Finding] = []
        for name, event in context.classes.items():
            if isinstance(event, ChangedEvent):
                for attr_name, attr in event.attributes.items():
                    if isinstance(attr, ChangedAttr):
                        if isinstance(attr.type, Change):
                            if attr.type.before == "integer_t" and attr.type.after == "long_t":
                                continue
                            findings.append(
                                ChangedTypeFinding(
                                    OcsfElementType.EVENT, name, attr_name, attr.type.before, attr.type.after
                                )
                            )

        for name, obj in context.objects.items():
            if isinstance(obj, ChangedObject):
                for attr_name, attr in obj.attributes.items():
                    if isinstance(attr, ChangedAttr):
                        if isinstance(attr.type, Change):
                            if attr.type.before == "integer_t" and attr.type.after == "long_t":
                                continue
                            findings.append(
                                ChangedTypeFinding(
                                    OcsfElementType.OBJECT, name, attr_name, attr.type.before, attr.type.after
                                )
                            )

        return findings
