"""A validation rule to identify changed attribute types."""

from dataclasses import dataclass

from ocsf.compare import Change, ChangedAttr, ChangedEvent, ChangedObject, Difference
from ocsf.schema import OcsfAttr, OcsfElementType
from ocsf.validate.framework import Finding, Rule, RuleMetadata

from .context import CompatibilityContext


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


class NoChangedTypesRule(Rule[CompatibilityContext]):
    def metadata(self):
        return RuleMetadata("No changed attribute types", description=_RULE_DESCRIPTION)

    def _check(
        self, name: str, attr_name: str, attr: Difference[OcsfAttr], context: CompatibilityContext
    ) -> None | ChangedTypeFinding:
        if isinstance(attr, ChangedAttr):
            if isinstance(attr.type, Change):
                # Expanding memory required is allowed. This would only break the most
                # stringent of encodings.
                if attr.type.before == "integer_t" and attr.type.after == "long_t":
                    return None

                # `string_t` -> `file_path_t`
                # PR#1326 reintroduced `file_path_t` and reassigned several
                # `string_t` attributes to `file_path_t`. This is technically
                # type narrowing and not backwards compatible, but it was
                # decided to allow this change on the OCSF Tuesday call. In the
                # future, we may want to limit this change to OCSF 1.4 -> 1.5.
                # if attr.type.before == "string_t" and attr.type.after == "file_path_t":
                #    return None

                if (
                    attr.type.after in context.after.types
                    and attr.type.before in context.before.types
                    and context.before.types[attr.type.before].type == context.after.types[attr.type.after].type
                ):
                    return None

                return ChangedTypeFinding(OcsfElementType.EVENT, name, attr_name, attr.type.before, attr.type.after)

    def validate(self, context: CompatibilityContext) -> list[Finding]:
        findings: list[Finding] = []
        for name, event in context.change.classes.items():
            if isinstance(event, ChangedEvent):
                for attr_name, attr in event.attributes.items():
                    finding = self._check(name, attr_name, attr, context)
                    if finding:
                        findings.append(finding)

        for name, obj in context.change.objects.items():
            if isinstance(obj, ChangedObject):
                for attr_name, attr in obj.attributes.items():
                    finding = self._check(name, attr_name, attr, context)
                    if finding:
                        findings.append(finding)

        return findings
