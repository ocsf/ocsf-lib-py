"""A validation rule to identify changed class UIDs."""

from dataclasses import dataclass
from ocsf.compare import ChangedSchema, NoChange, ChangedEvent, ChangedAttr, Removal, Addition
from ocsf.validate.framework import Rule, Finding, RuleMetadata


@dataclass
class ChangedClassUidFinding(Finding):
    event: str
    before: str
    after: str

    def message(self) -> str:
        return f"The Class ID of {self.event} changed from {self.before} to {self.after}"


_RULE_DESCRIPTION = """Class IDs are meant to be static identifiers for event
classes. They should never change. The most common cause of a changed class ID
is because the class was moved to a new category or from an extension to
core."""


class NoChangedClassUidsRule(Rule[ChangedSchema]):
    def metadata(self):
        return RuleMetadata("No changed class UIDs", description=_RULE_DESCRIPTION)

    def validate(self, context: ChangedSchema) -> list[Finding]:
        findings: list[Finding] = []
        for name, event in context.classes.items():
            if isinstance(event, ChangedEvent):
                if "class_uid" in event.attributes and isinstance(event.attributes["class_uid"], ChangedAttr):
                    uid = event.attributes["class_uid"]
                    if not isinstance(uid.enum, NoChange):
                        before: str | None = None
                        after: str | None = None
                        for k, v in uid.enum.items():
                            if isinstance(v, Removal):
                                before = k
                            elif isinstance(v, Addition):
                                after = k

                        if before is not None and after is not None:
                            findings.append(ChangedClassUidFinding(name, before, after))

        return findings
