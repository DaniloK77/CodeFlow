"""Scores: penalties, the syntax-error cap, points lost and metric limits."""

from __future__ import annotations

import pytest

from tools.codegrade.analyzer import build_report
from tools.codegrade.models import Dimension, FileReport, Finding, FunctionMetrics, Severity
from tools.codegrade.scoring import (
    SYNTAX_ERROR_CAP,
    Limit,
    metric_findings,
    points_lost,
    quality_score,
    round_score,
    score_findings,
    weighted_code_score,
)

from .helpers import make_source


def finding(rule: str, severity: Severity = Severity.WARNING) -> Finding:
    return Finding(rule, severity, "message", "a.ts", 1)


def file_report(path: str = "a.ts", **fields: object) -> FileReport:
    return FileReport(path=path, language="typescript", code_lines=100, **fields)  # type: ignore[arg-type]


def test_penalties_by_severity() -> None:
    findings = [
        finding("no-eval", Severity.ERROR),
        finding("no-var", Severity.WARNING),
        finding("todo-comment", Severity.INFO),
    ]
    assert score_findings(findings) == 100 - 15 - 7 - 3


def test_score_never_goes_negative() -> None:
    assert score_findings([finding("no-eval", Severity.ERROR)] * 20) == 0


def test_code_that_does_not_parse_is_capped() -> None:
    assert score_findings([finding("syntax-error", Severity.ERROR)]) == SYNTAX_ERROR_CAP
    many = [finding("syntax-error", Severity.ERROR)] * 5
    assert score_findings(many) == 100 - 5 * 15


@pytest.mark.parametrize(("value", "expected"), [(62.5, 63), (62.4, 62), (89.5, 90), (0.5, 1)])
def test_scores_round_half_up(value: float, expected: int) -> None:
    assert round_score(value) == expected


def test_code_score_is_weighted_by_lines_of_code() -> None:
    small = FileReport("a.ts", "typescript", code_lines=10, score=0)
    large = FileReport("b.ts", "typescript", code_lines=90, score=100)
    assert weighted_code_score([small, large]) == 90


def test_quality_blends_code_and_hygiene() -> None:
    assert quality_score(80, None) == 80
    assert quality_score(80, 40) == 70


def test_points_lost_add_up_to_the_deduction() -> None:
    findings = [
        finding("no-eval", Severity.ERROR),
        finding("complexity"),
        finding("magic-numbers", Severity.INFO),
        finding("no-tests"),
    ]
    lost = points_lost(findings, score_findings(findings))
    assert lost[Dimension.RELIABILITY.value] == 15
    assert lost[Dimension.TESTING.value] == 7
    assert sum(lost.values()) == 100 - score_findings(findings)


def test_points_lost_cover_the_syntax_error_cap() -> None:
    findings = [finding("syntax-error", Severity.ERROR)]
    lost = points_lost(findings, score_findings(findings))
    assert lost[Dimension.RELIABILITY.value] == 100 - SYNTAX_ERROR_CAP


def test_points_lost_are_scaled_when_a_file_bottoms_out() -> None:
    findings = [finding("no-eval", Severity.ERROR)] * 10
    assert sum(points_lost(findings, 0).values()) == 100


def test_limit_severity() -> None:
    limit = Limit(10, 20)
    assert limit.severity(10) is None
    assert limit.severity(11) is Severity.WARNING
    assert limit.severity(21) is Severity.ERROR


def test_long_complex_and_wide_functions_are_reported() -> None:
    function = FunctionMetrics("build", 1, 130, complexity=25, max_nesting=5, params=8)
    found = {f.rule: f.severity for f in metric_findings(file_report(functions=[function]), [])}
    assert found == {
        "function-length": Severity.ERROR,
        "complexity": Severity.ERROR,
        "deep-nesting": Severity.ERROR,
        "too-many-params": Severity.ERROR,
    }


def test_long_suite_callbacks_in_tests_are_not_long_functions() -> None:
    suite = FunctionMetrics("<anonymous>", 1, 300, complexity=1)
    report = file_report("src/App.test.tsx", functions=[suite])
    assert metric_findings(report, []) == []


def test_duplication_needs_both_volume_and_ratio() -> None:
    report = file_report()
    assert metric_findings(report, [5]) == []
    assert metric_findings(report, [5, 6, 7]) == []
    rules = [f.rule for f in metric_findings(report, list(range(1, 12)))]
    assert rules == ["duplication"]


def test_a_standalone_submission_without_tests_loses_points_for_it() -> None:
    source = make_source(
        """
        /** Adds two numbers. */
        export function add(first: number, second: number): number {
          return first + second;
        }
        """,
        "add.ts",
    )
    report = build_report([source], None, root_label="snippet")
    assert [f.rule for f in report.findings] == ["no-tests"]
    assert report.quality_score == 100 - Severity.WARNING.penalty
    assert report.points_lost[Dimension.TESTING.value] == Severity.WARNING.penalty


def test_tests_submitted_alongside_the_code_count() -> None:
    code = make_source(
        "/** Adds. */\nexport const add = (a1: number, b1: number): number => a1 + b1;\n", "add.ts"
    )
    tests = make_source("it('adds', () => { expect(add(1, 2)).toBe(3); });\n", "add.test.ts")
    report = build_report([code, tests], None, root_label="files")
    assert "no-tests" not in [f.rule for f in report.findings]
    assert report.quality_score == 100
