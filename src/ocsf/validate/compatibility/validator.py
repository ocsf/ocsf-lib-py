"""A backwards compatibility validator."""

from dataclasses import dataclass

from ocsf.compare import ChangedSchema
from ocsf.schema import OcsfSchema
from ocsf.validate.framework import Rule, Validator

from .added_required_attrs import NoAddedRequiredAttrsRule
from .changed_type import NoChangedTypesRule
from .increased_requirement import NoIncreasedRequirementsRule
from .removed_records import NoRemovedRecordsRule
from .removed_uids import NoChangedClassUidsRule

@dataclass
class CompatibilityContext:
    change: ChangedSchema
    before: OcsfSchema
    after: OcsfSchema
class CompatibilityValidator(Validator[CompatibilityContext]):
    def rules(self) -> list[Rule[CompatibilityContext]]:
        return [
            NoRemovedRecordsRule(),
            NoChangedClassUidsRule(),
            NoIncreasedRequirementsRule(),
            NoChangedTypesRule(),
            NoAddedRequiredAttrsRule(),
        ]
