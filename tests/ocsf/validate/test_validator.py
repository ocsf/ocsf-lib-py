from ocsf.validate.framework.validator import Severity, Finding, Rule, RuleMetadata, Validator


class FakeContext: ...


class FakeFinding(Finding):
    def message(self) -> str:
        return "Test finding message"


class FakeRule(Rule[FakeContext]):
    def metadata(self) -> RuleMetadata:
        return RuleMetadata("Test rule")

    def validate(self, context: FakeContext) -> list[Finding]:
        return [FakeFinding()]


class FakeValidator(Validator[FakeContext]):
    def rules(self) -> list[Rule[FakeContext]]:
        return [FakeRule()]


def test_validate():
    """Test basic validator functionality."""
    context = FakeContext()
    validator = FakeValidator(context)
    findings = validator.validate()

    assert isinstance(findings, dict)
    assert len(findings) == 1

    rule = list(findings.keys())[0]
    assert isinstance(findings[rule], list)
    assert len(findings[rule]) == 1
    assert isinstance(findings[rule][0], FakeFinding)
    assert findings[rule][0].severity == Severity.ERROR


def test_override_severity():
    """Test overriding the severity of a finding class."""
    context = FakeContext()
    validator = FakeValidator(context, {"FakeFinding": Severity.INFO})

    findings = validator.validate()
    rule = list(findings.keys())[0]
    assert isinstance(findings[rule], list)
    assert len(findings[rule]) == 1
    assert isinstance(findings[rule][0], FakeFinding)
    assert findings[rule][0].severity == Severity.INFO
