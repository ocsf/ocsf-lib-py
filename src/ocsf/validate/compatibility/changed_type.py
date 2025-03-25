"""A validation rule to identify changed attribute types."""

from dataclasses import dataclass
from ocsf.compare import Difference, ChangedSchema, Change, ChangedEvent, ChangedObject, ChangedAttr
from ocsf.schema import OcsfElementType, OcsfAttr
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

    def _check(self, name: str, attr_name: str, attr: Difference[OcsfAttr]) -> None | ChangedTypeFinding:
        if isinstance(attr, ChangedAttr):
            if isinstance(attr.type, Change):
                if attr.type.before == "integer_t" and attr.type.after == "long_t":
                    return None

                # `string_t` -> `file_path_t`
                # PR#1326 reintroduced `file_path_t` and reassigned several
                # `string_t` attributes to `file_path_t`. This is technically
                # type narrowing and not backwards compatible, but it was
                # decided to allow this change on the OCSF Tuesday call. In the
                # future, we may want to limit this change to OCSF 1.4 -> 1.5.
                if attr.type.before == "string_t" and attr.type.after == "file_path_t":
                    return None

                return ChangedTypeFinding(OcsfElementType.EVENT, name, attr_name, attr.type.before, attr.type.after)

    def validate(self, context: ChangedSchema) -> list[Finding]:
        findings: list[Finding] = []
        for name, event in context.classes.items():
            if isinstance(event, ChangedEvent):
                for attr_name, attr in event.attributes.items():
                    finding = self._check(name, attr_name, attr)
                    if finding:
                        findings.append(finding)

        for name, obj in context.objects.items():
            if isinstance(obj, ChangedObject):
                for attr_name, attr in obj.attributes.items():
                    finding = self._check(name, attr_name, attr)
                    if finding:
                        findings.append(finding)

        return findings
