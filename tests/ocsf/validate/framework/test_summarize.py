from ocsf.validate.framework.validator import Severity, Finding, Rule, RuleMetadata, ValidationFindings
from ocsf.validate.framework.summarize import count_severity, summarize_findings


class FakeFinding(Finding):
    def message(self) -> str:
        return "Test finding message"


class FakeRule(Rule[None]):
    def metadata(self) -> RuleMetadata:
        return RuleMetadata("Test rule")

    def validate(self, context: None) -> list[Finding]:
        return []


def mk_findings() -> ValidationFindings[None]:
    rule = FakeRule()
    findings: list[Finding] = []

    sevs: list[Severity] = []
    for sev in Severity:
        sevs.append(sev)

    for i in range(0, len(sevs) * 4):
        f = FakeFinding()
        f.severity = Severity(sevs[i % len(sevs)])
        findings.append(f)

    return {rule: findings}


def test_count_severity():
    """Verify that count_severity works as expected."""
    findings = mk_findings()
    for sev in Severity:
        assert count_severity(findings, sev) == 4


def test_summarize_findings():
    """Verify that summarize_findings works as expected."""
    findings = mk_findings()
    summary = summarize_findings(findings)

    assert isinstance(summary, dict)
    assert "Test rule" in summary
    assert isinstance(summary["Test rule"], dict)
    for sev in Severity:
        assert sev in summary["Test rule"]
        assert summary["Test rule"][sev] == 4
