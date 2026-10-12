"""Turns metrics into findings and findings into scores.

Every finding costs its file points (error 15, warning 7, info 3). A file's score is what is
left of 100, and a file that doesn't parse can't score above ``SYNTAX_ERROR_CAP``. "Points
lost" splits that deduction by dimension, so the breakdown always adds up to exactly the
points the file lost.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .models import Dimension, FileReport, Finding, Severity
from .source import is_test_file

SYNTAX_ERROR_CAP = 40  # code that doesn't run can't be judged on anything else
CODE_WEIGHT = 0.75  # for whole projects, the remaining 25% of quality is project hygiene


@dataclass(frozen=True)
class Limit:
    """Values above ``warning`` produce a warning; above ``error``, an error."""

    warning: float
    error: float

    def severity(self, value: float) -> Severity | None:
        """The severity ``value`` deserves, or None when it is within the limit."""
        if value > self.error:
            return Severity.ERROR
        if value > self.warning:
            return Severity.WARNING
        return None


@dataclass(frozen=True)
class Thresholds:
    # Defaults follow common linter conventions: ESLint max-lines, max-lines-per-function,
    # complexity (McCabe's classic limit of 10), max-depth and max-params.
    function_length: Limit = Limit(60, 120)
    complexity: Limit = Limit(10, 20)
    nesting: Limit = Limit(3, 4)
    params: Limit = Limit(5, 7)
    file_length: Limit = Limit(300, 500)
    duplication_ratio: Limit = Limit(0.05, 0.15)


DEFAULT_THRESHOLDS = Thresholds()


def round_score(value: float) -> int:
    """Rounds half up (62.5 → 63), the way people expect scores to round."""
    return math.floor(value + 0.5)


def score_findings(findings: list[Finding]) -> int:
    """100 minus every finding's penalty, never below zero; capped when the file doesn't parse."""
    score = max(0, 100 - sum(finding.severity.penalty for finding in findings))
    if any(finding.rule == "syntax-error" for finding in findings):
        return min(score, SYNTAX_ERROR_CAP)
    return score


def missing_tests_finding(path: str) -> Finding:
    """The finding for code that was submitted with no tests at all."""
    message = "no tests: nothing shows this code works; cover the main path and the edge cases"
    return Finding("no-tests", Severity.WARNING, message, path, 1)


def points_lost(findings: list[Finding], score: int) -> dict[str, float]:
    """Deduction per dimension, scaled so the parts add up to ``100 - score``."""
    raw = {dimension.value: 0.0 for dimension in Dimension}
    for finding in findings:
        raw[finding.dimension.value] += finding.severity.penalty
    total = sum(raw.values())
    if total == 0:
        return raw
    scale = (100 - score) / total
    return {dimension: round(value * scale, 1) for dimension, value in raw.items()}


def metric_findings(
    report: FileReport, duplicate_lines: list[int], limits: Thresholds = DEFAULT_THRESHOLDS
) -> list[Finding]:
    """Findings for measurements over their limits: size, complexity, nesting, duplication."""
    findings = [*_function_findings(report, limits), *_file_findings(report, limits)]
    duplication = _duplication_finding(report, duplicate_lines, limits)
    if duplication is not None:
        findings.append(duplication)
    return findings


def _function_findings(report: FileReport, limits: Thresholds) -> list[Finding]:
    findings = []
    in_tests = is_test_file(report.path)
    for function in report.functions:
        name = f"`{function.name}`"
        measurements = [
            ("complexity", limits.complexity, function.complexity, "cyclomatic complexity"),
            ("deep-nesting", limits.nesting, function.max_nesting, "nested control blocks"),
            ("too-many-params", limits.params, function.params, "parameters"),
        ]
        if not (in_tests and function.name == "<anonymous>"):
            # describe()/it() callbacks: a long test suite is not a long function.
            measurements.append(
                ("function-length", limits.function_length, function.length, "lines")
            )
        for rule, limit, value, unit in measurements:
            severity = limit.severity(value)
            if severity is not None:
                message = f"{name} has {value} {unit} (limit {limit.warning:g})"
                findings.append(Finding(rule, severity, message, report.path, function.start_line))
    return findings


def _file_findings(report: FileReport, limits: Thresholds) -> list[Finding]:
    severity = limits.file_length.severity(report.code_lines)
    if severity is None:
        return []
    message = f"{report.code_lines} lines of code (limit {limits.file_length.warning:g})"
    return [Finding("file-length", severity, message, report.path, 1)]


def _duplication_finding(
    report: FileReport, duplicate_lines: list[int], limits: Thresholds
) -> Finding | None:
    if len(duplicate_lines) < 2:
        return None
    ratio = len(duplicate_lines) / max(report.code_lines, 1)
    severity = limits.duplication_ratio.severity(ratio)
    if severity is None:
        return None
    message = (
        f"{len(duplicate_lines)} duplicated lines ({ratio:.0%} of the file); extract shared code"
    )
    return Finding("duplication", severity, message, report.path, duplicate_lines[0])


def _weights(reports: list[FileReport]) -> list[int]:
    return [max(report.code_lines, 1) for report in reports]


def weighted_code_score(reports: list[FileReport]) -> int:
    """Average file score, weighted by lines of code so large files count for more."""
    if not reports:
        return 100
    weights = _weights(reports)
    weighted = sum(report.score * weight for report, weight in zip(reports, weights, strict=True))
    return round_score(weighted / sum(weights))


def weighted_points_lost(reports: list[FileReport]) -> dict[str, float]:
    """Project-wide deduction per dimension, weighted the same way as the code score."""
    totals = {dimension.value: 0.0 for dimension in Dimension}
    if not reports:
        return totals
    weights = _weights(reports)
    for report, weight in zip(reports, weights, strict=True):
        for dimension, lost in report.points_lost.items():
            totals[dimension] += lost * weight
    return {dimension: round(value / sum(weights), 1) for dimension, value in totals.items()}


def quality_score(code_score: int, hygiene_score: int | None) -> int:
    """Code score alone, or 75% code + 25% hygiene when a whole project was analysed."""
    if hygiene_score is None:
        return code_score
    return round_score(CODE_WEIGHT * code_score + (1 - CODE_WEIGHT) * hygiene_score)
