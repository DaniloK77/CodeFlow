"""Glue between HTTP payloads and the codegrade engine. Framework-free and easy to test."""

from __future__ import annotations

import math
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from typing import Any

from tools.codegrade.analyzer import analyze_snippet, analyze_submission
from tools.codegrade.archive import ArchiveLimits, SkippedFile, read_archive
from tools.codegrade.assignment import (
    Assignment,
    Reviewer,
    ReviewOutcome,
    ReviewStatus,
    StaticCheck,
    grade_submission,
    run_review,
)
from tools.codegrade.hygiene import ProjectSnapshot
from tools.codegrade.models import ProjectReport
from tools.codegrade.report import submission_to_dict
from tools.codegrade.source import SourceFile

from .analysis import AnalysisRunner
from .quota import DailyQuota
from .schemas import SnippetReviewRequest

SECONDS_PER_HOUR = 3600
EXTENSIONS = {
    "typescript": ".ts",
    "tsx": ".tsx",
    "javascript": ".js",
    "jsx": ".jsx",
    "python": ".py",
}


@dataclass(frozen=True)
class ReviewContext:
    """Who is asking, and which reviewer and allowance apply to them."""

    reviewer: Reviewer | None
    quota: DailyQuota
    client: str
    analysis: AnalysisRunner


@dataclass(frozen=True)
class PreparedSubmission:
    """Source files ready for grading, plus what the archive reader left out."""

    sources: Sequence[SourceFile]
    snapshot: ProjectSnapshot | None
    label: str
    skipped: Sequence[SkippedFile] = ()


@dataclass(frozen=True)
class ArchiveUpload:
    data: bytes
    filename: str
    limits: ArchiveLimits


def review_snippet(request: SnippetReviewRequest, context: ReviewContext) -> dict[str, Any]:
    """Grades pasted code or a single file against its task and explanation.

    Raises ``UngradableInputError`` for text that isn't code in a supported language.
    """
    started = time.perf_counter()
    assignment = Assignment(request.task, request.explanation)
    label, quality, checks = context.analysis.run(
        analyze_snippet,
        request.code,
        assignment,
        filename=request.filename,
        extension=EXTENSIONS.get(request.language),
    )
    source = SourceFile.from_text(label, request.code)
    if source is None:  # analyze_snippet only accepts supported names
        raise ValueError(f"unsupported file type: {label}")
    prepared = PreparedSubmission([source], None, label)
    return _grade(prepared, quality, checks, assignment, context, started)


def review_archive(
    upload: ArchiveUpload, assignment: Assignment, context: ReviewContext
) -> dict[str, Any]:
    """Grades a zipped project, including project hygiene, against its task and explanation."""
    started = time.perf_counter()
    contents = read_archive(upload.data, upload.limits)
    prepared = PreparedSubmission(
        contents.sources, contents.snapshot, upload.filename, contents.skipped
    )
    quality, checks = context.analysis.run(
        analyze_submission, contents.sources, contents.snapshot, upload.filename, assignment
    )
    return _grade(prepared, quality, checks, assignment, context, started)


def _grade(
    prepared: PreparedSubmission,
    quality: ProjectReport,
    checks: tuple[StaticCheck, ...],
    assignment: Assignment,
    context: ReviewContext,
    started: float,
) -> dict[str, Any]:
    # The AI review (and its daily allowance) is only reached once the code has been accepted.
    outcome = _review_outcome(prepared.sources, assignment, context)
    report = grade_submission(quality, outcome, checks)
    source = "snippet" if prepared.snapshot is None else "archive"
    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    return {
        **submission_to_dict(report, source=source),
        "skipped": [asdict(item) for item in prepared.skipped],
        "duration_ms": elapsed_ms,
    }


def _review_outcome(
    sources: Sequence[SourceFile], assignment: Assignment, context: ReviewContext
) -> ReviewOutcome:
    """Runs the AI review if one is configured and the visitor has reviews left today."""
    if context.reviewer is None:
        return run_review(None, assignment, sources)
    wait = context.quota.acquire(context.client)
    if wait is not None:
        hours = max(1, math.ceil(wait / SECONDS_PER_HOUR))
        message = (
            f"You've used today's free AI reviews, so only code quality was graded. "
            f"More are available in about {hours} h."
        )
        return ReviewOutcome(ReviewStatus.LIMITED, message=message)
    outcome = run_review(context.reviewer, assignment, sources)
    if outcome.status is ReviewStatus.FAILED:
        context.quota.release(context.client)  # a failed review shouldn't use up the allowance
    return outcome
