from dataclasses import dataclass
from textwrap import wrap
from typing import Literal
from termcolor import colored
from .validator import Finding, ValidationFindings, Context, Severity
from .summarize import summarize_findings


class ValidationFormatter:
    def format_finding(self, finding: Finding) -> str:
        return f"  [{finding.severity.upper()}] {finding.message()}"

    def _heading(self, text: str) -> str:
        heading = f" {text}\n"
        heading += "-" * (len(text) * 2) + "\n"
        return heading

    def format(self, findings: ValidationFindings[Context], summarize: bool = True) -> str:
        output = ""
        for rule, rule_findings in findings.items():
            name = rule.metadata().name
            output += self._heading(name)

            if len(rule_findings) == 0:
                output += "  [SUCCESS] No findings\n"
            else:
                for finding in rule_findings:
                    output += self.format_finding(finding) + "\n"

            output += "\n"

        if summarize:
            summary = summarize_findings(findings)
            output += self._heading("Summary")

            for rule_name, rule_summary in summary.items():
                if rule_summary[Severity.ERROR] == 0 and rule_summary[Severity.FATAL] == 0:
                    output += "  [PASS] "
                else:
                    output += "  [FAIL] "
                output += (
                    rule_name
                    + ": "
                    + ", ".join([f"{severity}: {count}" for severity, count in rule_summary.items()])
                    + "\n"
                )

            output += "\n"

        return output


Color = Literal["red", "green", "yellow", "blue", "magenta", "cyan", "white"]
_SEVERITY_COLORS: dict[Severity, Color] = {
    Severity.ERROR: "red",
    Severity.FATAL: "red",
    Severity.WARNING: "yellow",
    Severity.INFO: "cyan",
}


def _color_severity(severity: Severity | Literal["SUCCESS"]) -> str:
    if severity == "SUCCESS":
        color = "green"
    else:
        color = _SEVERITY_COLORS[severity]
    return colored("[", "white") + colored(severity.upper(), color) + colored("]", "white")


@dataclass
class ColoringValidationFormatter(ValidationFormatter):
    line_length: int = 80

    def format_finding(self, finding: Finding) -> str:
        return f"  {_color_severity(finding.severity)} {finding.message()}"

    def _heading(self, text: str) -> str:
        heading = colored("╔", "cyan") + colored("═" * (len(text) + 2), "cyan") + colored("╗", "cyan") + "\n"
        heading += "║ " + colored(text, "white") + " ║\n"
        heading += colored("╚", "cyan") + colored("═" * (len(text) + 2), "cyan") + colored("╝", "cyan") + "\n"
        return heading

    def format(self, findings: ValidationFindings[Context], summarize: bool = True) -> str:
        output = ""
        for rule, rule_findings in findings.items():
            meta = rule.metadata()
            name = meta.name

            output += self._heading(name)

            if meta.description is not None:
                output += "\n".join(wrap(meta.description, width=self.line_length)) + "\n"

            output += "\n"

            if len(rule_findings) == 0:
                output += f"  {_color_severity('SUCCESS')} No findings\n"
            else:
                for finding in rule_findings:
                    output += self.format_finding(finding) + "\n"

            output += "\n"

        if summarize:
            summary = summarize_findings(findings)
            output += self._heading("Summary")

            for rule_name, rule_summary in summary.items():
                output += colored("  [ ", "white")
                if rule_summary[Severity.FATAL] > 0:
                    output += colored("💣 FAIL", _SEVERITY_COLORS[Severity.FATAL])
                elif rule_summary[Severity.ERROR] > 0:
                    output += colored("✗ FAIL", _SEVERITY_COLORS[Severity.ERROR])
                elif rule_summary[Severity.WARNING] > 0:
                    output += colored("! WARN", _SEVERITY_COLORS[Severity.WARNING])
                elif rule_summary[Severity.INFO] > 0:
                    output += colored("ℹ︎ PASS ", _SEVERITY_COLORS[Severity.INFO])
                else:
                    output += colored("✓ PASS", "green")
                output += colored(" ] ", "white") + rule_name + "\n"

            output += "\n"

        return output
