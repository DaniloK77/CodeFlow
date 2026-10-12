"""The JSON report contract, shared by the CLI (``--format json``) and the HTTP API."""

from __future__ import annotations

import json
from dataclasses import asdict
from enum import Enum
from typing import Any

from . import __version__
from .assignment import AIReview, SubmissionReport
from .models import FileReport, Finding, ProjectReport

_EMPTY_REVIEW: dict[str, Any] = {
    "model": None,
    "summary": None,
    "requirements": [],
    "bugs": [],
    "explanation": None,
    "strengths": [],
    "improvements": [],
    "files_reviewed": 0,
    "files_omitted": [],
}


def render_json(report: SubmissionReport, *, source: str) -> str:
    """Pretty-printed :func:`submission_to_dict`."""
    return json.dumps(submission_to_dict(report, source=source), indent=2, ensure_ascii=False)


def submission_to_dict(report: SubmissionReport, *, source: str) -> dict[str, Any]:
    """Everything about one graded submission, as plain JSON-ready data."""
    payload = {
        "tool": "codegrade",
        "version": __version__,
        "source": source,
        "name": report.quality.root,
        "verdict": report.verdict,
        "grade": report.grade,
        "overall_score": report.overall_score,
        "weights": dict(report.weights),
        "scores": {
            "task": report.task_score,
            "quality": report.quality.quality_score,
            "explanation": report.explanation_score,
        },
        "review": _review_json(report),
        "checks": [asdict(check) for check in report.checks],
        "quality": quality_to_dict(report.quality),
    }
    return json.loads(json.dumps(payload, default=_json_default))


def quality_to_dict(project: ProjectReport) -> dict[str, Any]:
    """Static code-quality part of the report."""
    return {
        "score": project.quality_score,
        "code_score": project.code_score,
        "hygiene_score": project.hygiene_score,
        "points_lost": project.points_lost,
        "files": [_file_json(report) for report in project.files],
        "hygiene": [asdict(check) for check in project.hygiene],
    }


def _review_json(report: SubmissionReport) -> dict[str, Any]:
    outcome = report.outcome
    review: AIReview | None = outcome.review
    data: dict[str, Any] = {"status": outcome.status.value, "message": outcome.message}
    if review is None:
        return {**data, **_EMPTY_REVIEW}
    return {
        **data,
        "model": review.model,
        "summary": review.summary,
        "requirements": [asdict(item) for item in review.requirements],
        "bugs": [asdict(bug) for bug in review.bugs],
        "explanation": asdict(review.explanation),
        "strengths": list(review.strengths),
        "improvements": list(review.improvements),
        "files_reviewed": review.files_reviewed,
        "files_omitted": list(review.files_omitted),
    }


def _file_json(report: FileReport) -> dict[str, Any]:
    data = asdict(report)
    data["findings"] = [_finding_json(finding) for finding in report.findings]
    data["longest_function"] = report.longest_function
    data["max_complexity"] = report.max_complexity
    return data


def _finding_json(finding: Finding) -> dict[str, Any]:
    return {**asdict(finding), "dimension": finding.dimension.value}


def _json_default(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"not JSON serialisable: {type(value).__name__}")
