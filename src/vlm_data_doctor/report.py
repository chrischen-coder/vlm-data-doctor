"""Stable, content-free report records and renderers."""

from collections import Counter
from dataclasses import asdict, dataclass, field
import json


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    dataset: str
    row: int
    field: str
    message: str


@dataclass
class Report:
    records: dict[str, int] = field(default_factory=dict)
    issues: list[Issue] = field(default_factory=list)
    unique_image_files: int = 0
    provenance: dict = field(default_factory=dict)

    def add(self, severity: str, code: str, dataset: str, row: int,
            field: str, message: str) -> None:
        self.issues.append(Issue(severity, code, dataset, row, field, message))

    @property
    def errors(self) -> int:
        return sum(i.severity == "error" for i in self.issues)

    @property
    def warnings(self) -> int:
        return sum(i.severity == "warning" for i in self.issues)

    def to_dict(self) -> dict:
        return {
            "schema_version": "1.1",
            "provenance": self.provenance,
            "summary": {
                "records": self.records,
                "unique_image_files": self.unique_image_files,
                "errors": self.errors,
                "warnings": self.warnings,
                "by_code": dict(sorted(Counter(i.code for i in self.issues).items())),
            },
            "issues": [asdict(i) for i in self.issues],
        }

    def render(self, output_format: str = "text") -> str:
        if output_format == "html":
            from .html_report import render_html
            return render_html(self)
        if output_format not in {"text", "json", "markdown"}:
            raise ValueError(f"Unsupported report format: {output_format}")
        if output_format == "json":
            return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
        counts = ", ".join(f"{k}={v}" for k, v in self.records.items())
        summary = (f"Records: {counts}\nUnique image files: {self.unique_image_files}\n"
                   f"Errors: {self.errors} | Warnings: {self.warnings}")
        if output_format == "markdown":
            lines = ["# VLM Data Doctor report", "", summary.replace("\n", "  \n"), "",
                     "| Severity | Rule | Location | Advice |",
                     "| --- | --- | --- | --- |"]
            for issue in self.issues:
                values = [issue.severity, issue.code,
                          f"{issue.dataset}:{issue.row} {issue.field}", issue.message]
                lines.append("| " + " | ".join(v.replace("|", "\\|") for v in values) + " |")
            if not self.issues:
                lines.extend(["", "No issues found by the supported checks."])
            return "\n".join(lines)
        lines = ["VLM Data Doctor", summary]
        for issue in self.issues:
            lines.append(f"{issue.severity.upper()} {issue.code} "
                         f"{issue.dataset}:{issue.row} {issue.field}: {issue.message}")
        if not self.issues:
            lines.append("No issues found by the supported checks.")
        return "\n".join(lines)
