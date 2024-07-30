"""A validation rule to identify removed or renamed objects, events, attributes, and enums.

There are separate Finding classes for removal and renaming of each type of
record. This is to allow for flexibility in configuring the severity of the
findings.

Renaming is detected when an element is removed *and* an element with the same
caption or class_uid is added to the same set.
"""

from dataclasses import dataclass
from typing import Optional, Literal

from ocsf.schema import OcsfElementType
from ocsf.compare import ChangedSchema, Removal, Addition, ChangedEvent, ChangedObject, ChangedAttr
from ocsf.validate.framework import Rule, Finding, RuleMetadata


def _path(
    root: Literal[OcsfElementType.OBJECT] | Literal[OcsfElementType.EVENT],
    name: str,
    path: Optional[str | tuple[str, ...]],
) -> str:
    """Format a path to a schema element."""
    path_str = root + ":"
    if path is not None:
        if isinstance(path, tuple):
            path_str += ".".join(path)
        else:
            path_str += "path"
        path_str += "."
    return f"{path_str}{name}"


@dataclass
class RemovedRecordFinding(Finding):
    """A finding for a removed object, event, attribute, or enum member."""

    name: str
    caption: str
    root: Literal[OcsfElementType.EVENT] | Literal[OcsfElementType.OBJECT] = OcsfElementType.EVENT
    path: Optional[str | tuple[str, ...]] = None

    def _root(self) -> Literal[OcsfElementType.EVENT] | Literal[OcsfElementType.OBJECT]:
        return self.root

    def message(self) -> str:
        return f"{_path(self._root(), self.name, self.path)} ({self.caption}) was removed"


class RemovedEventFinding(RemovedRecordFinding): ...


class RemovedAttrFinding(RemovedRecordFinding): ...


class RemovedEnumMemberFinding(RemovedRecordFinding): ...


class RemovedObjectFinding(RemovedRecordFinding):
    def _root(self) -> Literal[OcsfElementType.EVENT] | Literal[OcsfElementType.OBJECT]:
        return OcsfElementType.OBJECT


@dataclass
class RenamedRecordFinding(Finding):
    """A finding for a renamed object, event, attribute, or enum member."""

    before: str
    after: str
    caption: str
    root: Literal[OcsfElementType.EVENT] | Literal[OcsfElementType.OBJECT] = OcsfElementType.EVENT
    path: Optional[str | tuple[str, ...]] = None

    def _root(self) -> Literal[OcsfElementType.EVENT] | Literal[OcsfElementType.OBJECT]:
        return self.root

    def message(self) -> str:
        return f"{_path(self._root(), self.before, self.path)} ({self.caption}) appears to have been renamed to {_path(self._root(), self.after, self.path)}"


class RenamedEventFinding(RenamedRecordFinding): ...


class RenamedAttrFinding(RenamedRecordFinding): ...


class RenamedEnumMemberFinding(RenamedRecordFinding): ...


class RenamedObjectFinding(RenamedRecordFinding):
    def _root(self) -> Literal[OcsfElementType.EVENT] | Literal[OcsfElementType.OBJECT]:
        return OcsfElementType.OBJECT


_RULE_DESCRIPTION = """Removing event and object types can rather obviously
break compatibility between schemas, as can removing attributes of events and
objects or members of enumerations. Instead of removing these elements, consider
deprecating them instead. Renaming elements is a special case of removal: the
old name is removed and a new name is added. This has the same effect as
removal, and so is still a breaking change.
"""


class NoRemovedRecordsRule(Rule[ChangedSchema]):
    """A rule to identify removed or renamed objects, events, attributes, and enums."""

    def metadata(self):
        return RuleMetadata("No removed or renamed schema elements", description=_RULE_DESCRIPTION)

    def validate(self, context: ChangedSchema) -> list[Finding]:
        """Search changed objects and events in the schema to identify any removed or renamed elements."""

        # This rule has a lot of loops. It could be rewritten as one large outer
        # loop, but it's intentionally separated into three outer loops for
        # readability (and perhaps should be separated into more). Those loops
        # implement the following operations:
        #   1. Search for renamed or removed events
        #   2. Search for renamed or removed objects
        #   3. Search for renamed or removed attributes and enum members
        #

        findings: list[Finding] = []

        ###
        # Loop 1: Search for renamed or removed events
        #
        # Psuedo code:
        # for each removed event:
        #     for each added event:
        #         if added event has same caption or class_uid as removed event:
        #             add renamed event finding
        #     if no renamed event finding was added:
        #         add removed event finding
        for name, event in context.classes.items():
            if isinstance(event, Removal):
                found = False
                for _, added in context.classes.items():
                    if isinstance(added, Addition):
                        # An addition with the same caption or class_uid as the removed event is probably a rename
                        if (added.after.caption == event.before.caption) or (
                            "class_uid" in added.after.attributes
                            and "class_uid" in event.before.attributes
                            and added.after.attributes["class_uid"] == event.before.attributes["class_uid"]
                        ):
                            findings.append(
                                RenamedEventFinding(event.before.name, added.after.name, event.before.caption)
                            )
                            found = True
                            break

                if not found:
                    findings.append(RemovedEventFinding(name, event.before.caption))

        ###
        # Loop 2: Search for renamed or removed objects
        #
        # Psuedo code:
        # for each removed object:
        #     for each added object:
        #         if added object has same caption as removed object:
        #             add renamed object finding
        #     if no renamed object finding was added:
        #         add removed object finding
        for name, obj in context.objects.items():
            if isinstance(obj, Removal):
                found = False
                for _, added in context.objects.items():
                    if isinstance(added, Addition):
                        # An addition with the same caption as the removed object is probably a rename
                        if added.after.caption == obj.before.caption:
                            findings.append(RenamedObjectFinding(obj.before.name, added.after.name, obj.before.caption))
                            found = True
                            break

                if not found:
                    findings.append(RemovedObjectFinding(name, obj.before.caption))

        ###
        # Loop 3: Search for renamed or removed attributes and enum members
        #
        # Psuedo code:
        # for each changed event or object:
        #    for each attribute:
        #        if attribute was removed:
        #           for each added attribute:
        #               if added attribute has same caption as removed attribute:
        #                   add renamed attribute finding
        #           if no renamed attribute finding was added:
        #               add removed attribute finding
        #
        #        if attribute was changed and has an enum:
        #            for each enum member:
        #                if enum member was removed:
        #                    for each added enum member:
        #                        if added enum member has same caption as removed enum member:
        #                            add renamed enum member finding
        #                    if no renamed enum member finding was added:
        #                        add removed enum member finding
        #

        # First, build a combined list of changed events and objects
        changed_records = [
            (name, OcsfElementType.EVENT, event)
            for name, event in context.classes.items()
            if isinstance(event, ChangedEvent)
        ] + [
            (name, OcsfElementType.OBJECT, obj)
            for name, obj in context.objects.items()
            if isinstance(obj, ChangedObject)
        ]

        # Now loop over that list
        for name, kind, record in changed_records:
            assert kind == OcsfElementType.EVENT or kind == OcsfElementType.OBJECT
            for attr_name, attr in record.attributes.items():
                if isinstance(attr, Removal):
                    # Before calling the attribute removed, look to see if it's been renamed
                    found = False
                    for added_name, added in record.attributes.items():
                        if isinstance(added, Addition) and added.after.caption == attr.before.caption:
                            findings.append(RenamedAttrFinding(attr_name, added_name, attr.before.caption, kind, name))
                            found = True
                            break

                    # Nope, it was removed
                    if not found:
                        findings.append(RemovedAttrFinding(attr_name, attr.before.caption, kind, name))

                elif isinstance(attr, ChangedAttr) and isinstance(attr.enum, dict):
                    # The attribute was changed; were any enum members removed or renamed?
                    for member_key, member in attr.enum.items():
                        if isinstance(member, Removal):
                            # Before calling the enum member removed, look to see if it's been renamed
                            found = False
                            for added_key, added in attr.enum.items():
                                if isinstance(added, Addition) and added.after.caption == member.before.caption:
                                    findings.append(
                                        RenamedEnumMemberFinding(
                                            member_key, added_key, member.before.caption, kind, (name, attr_name)
                                        )
                                    )
                                    found = True
                                    break

                            # Nope, it was removed
                            if not found:
                                findings.append(
                                    RemovedEnumMemberFinding(member_key, member.before.caption, kind, (name, attr_name))
                                )

        return findings
