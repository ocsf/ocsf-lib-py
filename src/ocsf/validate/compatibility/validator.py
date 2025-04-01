"""A backwards compatibility validator."""

from ocsf.validate.framework import Rule, Validator

from .added_required_attrs import NoAddedRequiredAttrsRule
from .changed_type import NoChangedTypesRule
from .context import CompatibilityContext
from .increased_requirement import NoIncreasedRequirementsRule
from .removed_records import NoRemovedRecordsRule
from .removed_uids import NoChangedClassUidsRule


class CompatibilityValidator(Validator[CompatibilityContext]):
    def rules(self) -> list[Rule[CompatibilityContext]]:
        return [
            NoRemovedRecordsRule(),
            NoChangedClassUidsRule(),
            NoIncreasedRequirementsRule(),
            NoChangedTypesRule(),
            NoAddedRequiredAttrsRule(),
        ]
