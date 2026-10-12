"""Terminal rendering of a graded submission: review, code quality and the final grade."""

from __future__ import annotations

from . import __version__
from .assignment import (
    EXCELLENT_MIN,
    GOOD_MIN,
    WEIGHTS,
    AIReview,
    ReviewStatus,
    StaticCheck,
    SubmissionReport,
)
from .models import FileReport, Finding, Grade, ProjectReport, Severity

DEFAULT_FINDING_LIMIT = 20
_RULE = "─" * 64
_SEVERITY_ICONS = {Severity.ERROR: "✖", Severity.WARNING: "▲", Severity.INFO: "•"}
_STATUS_ICONS = {"met": "✔", "partial": "◐", "missing": "✖", "found": "✔", "mismatch": "◐"}
_ANSI_CODES = {"bold": "1", "dim": "2", "red": "31", "green": "32", "yellow": "33", "cyan": "36"}
_TABLE_COLUMNS = ("LOC", 5), ("FN", 3), ("MAX LEN", 7), ("MAX CC", 6), ("SCORE", 5)


class Palette:
    """ANSI styling that disappears entirely when colour is off (pipes, CI logs, NO_COLOR)."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def __call__(self, text: str, *styles: str) -> str:
        """``text`` wrapped in the given ANSI styles (unchanged when colour is off)."""
        if not self.enabled or not styles:
            return text
        codes = ";".join(_ANSI_CODES[style] for style in styles)
        return f"\033[{codes}m{text}\033[0m"

    def grade(self, grade: Grade, text: str | None = None) -> str:
        """A grade in its traffic-light colour."""
        colour = {Grade.EXCELLENT: "green", Grade.GOOD: "yellow", Grade.POOR: "red"}[grade]
        return self(text or grade.value, "bold", colour)

    def severity(self, severity: Severity, text: str) -> str:
        """Text in the colour of a finding severity."""
        colour = {Severity.ERROR: "red", Severity.WARNING: "yellow", Severity.INFO: "dim"}[severity]
        return self(text, colour)


def render_text(report: SubmissionReport, *, color: bool = False, verbose: bool = False) -> str:
    """The full terminal report for one graded submission."""
    paint = Palette(color)
    project = report.quality
    sections = [
        _header(project, paint),
        *_review_sections(report, paint),
        _checks(report.checks, paint),
        _file_table(project.files, paint),
        _findings(project.findings, paint, verbose),
        _hygiene(project, paint),
        _summary(report, paint),
    ]
    return "\n\n".join(section for section in sections if section)


def _header(project: ProjectReport, paint: Palette) -> str:
    lines = sum(report.code_lines for report in project.files)
    title = paint(f"codegrade {__version__}", "bold", "cyan") + " · code review"
    details = f"{project.root} · {len(project.files)} files · {lines:,} lines of code"
    return f"{title}\n{paint(details, 'dim')}"


def _review_sections(report: SubmissionReport, paint: Palette) -> list[str]:
    outcome = report.outcome
    if outcome.status is ReviewStatus.NOT_REQUESTED:
        return []
    if outcome.review is None:
        return [paint(f"  AI REVIEW  {outcome.status.value}: {outcome.message}", "yellow")]
    review = outcome.review
    return [
        _task_section(review, report.task_score, paint),
        _explanation_section(review, report.explanation_score, paint),
        _feedback_section(review, paint),
    ]


def _task_section(review: AIReview, score: int | None, paint: Palette) -> str:
    lines = [paint(f"  TASK  {score}/100", "bold")]
    for item in review.requirements:
        icon = _STATUS_ICONS[item.status]
        lines.append(f"  {icon} {item.requirement}  {paint(item.evidence, 'dim')}")
    for bug in review.bugs:
        lines.append(paint(f"  ✖ bug ({bug.severity}) {bug.location}: {bug.description}", "red"))
    return "\n".join(lines)


def _explanation_section(review: AIReview, score: int | None, paint: Palette) -> str:
    assessment = review.explanation
    ratings = f"{assessment.accuracy} · {assessment.completeness} · {assessment.clarity}"
    return "\n".join(
        [
            paint(f"  EXPLANATION  {score}/100", "bold") + paint(f"  ({ratings})", "dim"),
            f"  {assessment.feedback}",
        ]
    )


def _feedback_section(review: AIReview, paint: Palette) -> str:
    lines = [paint("  MENTOR FEEDBACK", "bold"), f"  {review.summary}"]
    lines += [paint(f"  + {strength}", "green") for strength in review.strengths]
    lines += [paint(f"  → {improvement}", "yellow") for improvement in review.improvements]
    if review.files_omitted:
        lines.append(
            paint(f"  (not sent to the reviewer: {', '.join(review.files_omitted)})", "dim")
        )
    return "\n".join(lines)


def _checks(checks: tuple[StaticCheck, ...], paint: Palette) -> str:
    if not checks:
        return ""
    lines = [
        paint("  STATIC CHECKS  names from the task and explanation, looked up in the code", "bold")
    ]
    for check in checks:
        icon = _STATUS_ICONS[check.status]
        lines.append(f"  {icon} {check.source}: `{check.name}`  {paint(check.detail, 'dim')}")
    return "\n".join(lines)


def _file_table(files: list[FileReport], paint: Palette) -> str:
    width = max([len("FILE"), *(len(report.path) for report in files)])
    columns = "".join(f"  {title:>{size}}" for title, size in _TABLE_COLUMNS)
    rows = [paint(f"  {'FILE':<{width}}{columns}", "dim")]
    for report in files:
        rows.append(
            f"  {report.path:<{width}}  {report.code_lines:>5}  {len(report.functions):>3}"
            f"  {report.longest_function:>7}  {report.max_complexity:>6}  {report.score:>5}"
        )
    return "\n".join(rows)


def _findings(findings: list[Finding], paint: Palette, verbose: bool) -> str:
    if not findings:
        return paint("  No findings.", "green")
    shown = findings if verbose else [f for f in findings if f.severity is not Severity.INFO]
    shown = shown if verbose else shown[:DEFAULT_FINDING_LIMIT]
    width = max((len(f"{finding.path}:{finding.line}") for finding in shown), default=0)
    lines = [paint(f"  FINDINGS  {_severity_counts(findings)}", "bold")]
    lines += [_finding_line(finding, width, paint) for finding in shown]
    if len(shown) < len(findings):
        hidden = len(findings) - len(shown)
        lines.append(paint(f"  … {hidden} more (run with --verbose to list everything)", "dim"))
    return "\n".join(lines)


def _severity_counts(findings: list[Finding]) -> str:
    counts = {severity: sum(f.severity is severity for f in findings) for severity in Severity}
    return " · ".join(f"{count} {severity.value}" for severity, count in counts.items() if count)


def _finding_line(finding: Finding, width: int, paint: Palette) -> str:
    icon = paint.severity(finding.severity, _SEVERITY_ICONS[finding.severity])
    location = f"{finding.path}:{finding.line}"
    rule = paint(f"{finding.rule:<21}", "cyan")
    return f"  {icon} {location:<{width}}  {rule}  {finding.message}"


def _hygiene(project: ProjectReport, paint: Palette) -> str:
    if project.hygiene_score is None:
        return ""
    marks = [
        (paint("✔", "green") if check.passed else paint("✖", "red")) + f" {check.name}"
        for check in project.hygiene
    ]
    lines = [
        paint(f"  PROJECT HYGIENE  {project.hygiene_score}/100", "bold"),
        "  " + "   ".join(marks),
    ]
    lines += [
        paint(f"    → {check.name}: {check.hint}", "dim")
        for check in project.hygiene
        if not check.passed
    ]
    return "\n".join(lines)


def _summary(report: SubmissionReport, paint: Palette) -> str:
    project = report.quality
    rows = [paint(_RULE, "dim")]
    if report.grade is None or report.overall_score is None:
        rows.append(paint(f"  CODE QUALITY   {project.quality_score:>3}/100", "bold"))
        rows.append(paint("  Task not verified: no rank without an AI review of the task", "dim"))
        return "\n".join([*rows, paint(_RULE, "dim")])
    rows += [
        f"  Task           {report.task_score:>3}/100   ({WEIGHTS['task']}%)",
        f"  Code quality   {project.quality_score:>3}/100   ({WEIGHTS['quality']}%)",
        f"  Explanation    {report.explanation_score:>3}/100   ({WEIGHTS['explanation']}%)",
    ]
    overall = f"  OVERALL        {report.overall_score:>3}/100   →   "
    rows.append(paint(overall, "bold") + paint.grade(report.grade))
    legend = f"  Excellent ≥ {EXCELLENT_MIN} · Good ≥ {GOOD_MIN} · Poor < {GOOD_MIN}"
    return "\n".join([*rows, paint(legend, "dim"), paint(_RULE, "dim")])
