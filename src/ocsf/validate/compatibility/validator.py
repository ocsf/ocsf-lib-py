"""A backwards compatibility validator."""

from ocsf.compare import ChangedSchema
from ocsf.validate.framework import Rule, Validator

from .changed_type import NoChangedTypesRule
from .increased_requirement import NoIncreasedRequirementsRule
from .removed_records import NoRemovedRecordsRule
from .removed_uids import NoChangedClassUidsRule
from .added_required_attrs import NoAddedRequiredAttrsRule


class CompatibilityValidator(Validator[ChangedSchema]):
    def rules(self) -> list[Rule[ChangedSchema]]:
        return [
            NoRemovedRecordsRule(),
            NoChangedClassUidsRule(),
            NoIncreasedRequirementsRule(),
            NoChangedTypesRule(),
            NoAddedRequiredAttrsRule(),
        ]
