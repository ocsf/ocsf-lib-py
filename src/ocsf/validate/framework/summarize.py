from .validator import Severity, ValidationFindings, Context


def count_severity(findings: ValidationFindings[Context], severity: Severity) -> int:
    """Count the number of findings with a given severity.

    Args:
        findings: A mapping of rules to findings as is produced by Validator.validate.
        severity: The severity level to count.

    Returns:
        The number of findings with the given severity.
    """
    count = 0
    for rule_findings in findings.values():
        for finding in rule_findings:
            if finding.severity == severity:
                count += 1

    return count


FindingSummary = dict[str, dict[Severity, int]]


def summarize_findings(findings: ValidationFindings[Context]) -> FindingSummary:
    """Summarize the findings produced by a validator.

    Args:
        findings: A mapping of rules to findings as is produced by Validator.validate.

    Returns:
        A tally by rule name and severity level. Example: dict["rule name", {"info": 0, "warning": 11, ...}]
    """
    summary: dict[str, dict[Severity, int]] = {}

    for rule, rule_findings in findings.items():
        rule_name = rule.metadata().name
        summary[rule_name] = {}

        for sev in Severity:
            summary[rule_name][sev] = 0

        for finding in rule_findings:
            summary[rule_name][finding.severity] += 1

    return summary
