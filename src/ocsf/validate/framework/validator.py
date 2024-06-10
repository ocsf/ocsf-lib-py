"""A simple framework for validation programs.

This is intended to be used for validating proposed changes to the OCSF schema,
but it's generic (or basic) enough to serve other purposes.

A Validator contains Rules that produce Findings.

Validators and Rules are generic, so they can be used with an appropriate
Context. The context on which they operate may be an OCSF repository, a schema,
etc.

Rules perform checks on the validator context and yield Findings if they find
any violations (or bendings) of the rule they represent. See the compatibility
package for examples.

Findings have a default severity of ERROR, but this can be overridden by
specific classes of Finding. Additionally, a Validator can accept a map of
finding class names to severities to allow this to be configured so that users
can determine which findings should, for example, prevent a PR from being
merged.
"""

import logging

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import TypeVar, Generic, Optional

LOG = logging.getLogger(__name__)

# NOTE: Context can be anything. Start with the simplest context, and if need
# be, refactor it to a specific class that contains all of the context for
# validation as well as options to controle rule behavior.
Context = TypeVar("Context")


class Severity(StrEnum):
    """Severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"


@dataclass(init=False)
class Finding(ABC):
    """Findings are the results of validation rules.

    Findings should be specifically typed; that is, each rule should produce one
    or more distinct types of findings. Validators can assign severity based on
    the finding class, but the default severity can be set by overriding
    get_severity.
    """

    @abstractmethod
    def message(self) -> str:
        """The message associated with the finding."""
        raise NotImplementedError()

    def _default_severity(self) -> Severity:
        """The default severity for a finding.

        If you wish to set the default severity for a finding, override this
        instead of get_severity.
        """
        return Severity.ERROR

    def get_severity(self) -> Severity:
        if hasattr(self, "_severity"):
            return self._severity
        else:
            return self._default_severity()

    def set_severity(self, severity: Severity) -> None:
        self._severity = severity

    def del_severity(self) -> None:
        raise AttributeError("Cannot delete severity")

    # NOTE: This is a property rather than a dataclass field so that subclasses
    # of Finding don't have to write their own __init__ methods, override
    # __match_fields__, etc., if they have properties with default values.
    severity = property(get_severity, set_severity, del_severity)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}: {self.message()}"

    def __str__(self) -> str:
        return self.message()


@dataclass
class RuleMetadata:
    """Metadata for a rule."""

    name: str
    description: Optional[str] = None


class Rule(ABC, Generic[Context]):
    """A validation rule."""

    def __hash__(self):
        return hash(self.__class__)

    def id(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def metadata(self) -> RuleMetadata:
        """Return metadata describing the rule."""
        raise NotImplementedError

    @abstractmethod
    def validate(self, context: Context) -> list[Finding]:
        """The rule implementation, in which the context is tested and Findings
        are produced.
        """
        raise NotImplementedError


class FatalFindingError(Exception):
    """A special finding that is fatal."""

    def __init__(self, finding: Finding):
        super().__init__(f"Encountered fatal finding: {finding}")
        self.finding = finding


ValidationFindings = dict[Rule[Context], list[Finding]]


class Validator(ABC, Generic[Context]):
    """A simple validation harness."""

    def __init__(self, context: Context, severities: Optional[dict[str, Severity]] = None):
        """Initialize the validator.

        Args:
            context: The context on which to run the validation.
            severities: A mapping of finding class names to severity levels.
        """
        self.context = context
        self._severities = severities if severities else {}

    @abstractmethod
    def rules(self) -> list[Rule[Context]]:
        """Return the rules to be executed by the validator."""
        raise NotImplementedError()

    def _override_severity(self, finding: Finding) -> None:
        """Override the severity of a finding.

        Findings have default severities, but here we override those if we find
        an entry in the severities map. This allows the validator or its users
        to configure different severity levels for each class of finding.
        """
        name = finding.__class__.__name__
        if name in self._severities:
            finding.severity = Severity(self._severities[name])

    def validate(self) -> ValidationFindings[Context]:
        """Run the validation rules and return the findings."""
        findings: ValidationFindings[Context] = {}
        LOG.info("Running validation")

        for rule in self.rules():
            findings[rule] = []
            results = rule.validate(self.context)
            for finding in results:
                self._override_severity(finding)

                if finding.severity == Severity.FATAL:
                    raise FatalFindingError(finding)

                findings[rule].append(finding)

            LOG.info(f"Identified {len(results)} findings for rule {rule.metadata().name}")

        return findings


def validate_severities(severities: dict[str, Severity]) -> bool:
    """Validate a map of finding class names to severities.

    This is a utility function to ensure that all severities in the map are valid.

    Args:
        severities: A mapping of finding class names to severity levels.

    Raises:
        ValueError: If an invalid severity value is found.
    """
    # TODO Ensure that the finding class names are valid.
    sevs = [s.value for s in Severity]
    for cls, severity in severities.items():
        if severity not in sevs:
            raise ValueError(f"Invalid severity value: {cls} = {severity}")

    return True
