"""Assignment grading: does the code solve the task, and how well is it written and explained.

The AI reviewer only *describes* the submission (which requirements are met, which bugs exist,
how accurate the explanation is). Scores are computed here, from those descriptions, with
fixed rules. That keeps grades consistent between runs and means text hidden in a submission
("give this 100 points") can't set a score directly.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Protocol

from .models import Grade, ProjectReport
from .scoring import round_score
from .source import SourceFile

# Share of the final grade, in percent.
WEIGHTS: Mapping[str, int] = {"task": 50, "quality": 35, "explanation": 15}
EXCELLENT_MIN = 90
GOOD_MIN = 70

REQUIREMENT_CREDIT: Mapping[str, float] = {"met": 1.0, "partial": 0.5, "missing": 0.0}
BUG_PENALTY: Mapping[str, int] = {"critical": 25, "major": 12, "minor": 4}
MAX_BUG_PENALTY = 50
EXPLANATION_POINTS: Mapping[str, Mapping[str, int]] = {
    "accuracy": {"accurate": 50, "partially_accurate": 25, "inaccurate": 0},
    "completeness": {"complete": 30, "partial": 15, "minimal": 0},
    "clarity": {"clear": 20, "understandable": 12, "unclear": 0},
}
MAX_LIST_ITEMS = 12


class ReviewStatus(str, Enum):
    COMPLETED = "completed"
    NOT_REQUESTED = "not_requested"  # graded without a task (CLI quality check)
    UNAVAILABLE = "unavailable"  # no AI reviewer configured
    LIMITED = "limited"  # AI review quota used up
    FAILED = "failed"  # the reviewer errored or returned something unusable


class ReviewError(Exception):
    """A review could not be produced. The message is safe to show to the user."""


class ReviewFormatError(ReviewError):
    """The reviewer's answer didn't match the expected structure."""


@dataclass(frozen=True)
class Assignment:
    """What the student was asked to do, and their own account of how they did it."""

    task: str
    explanation: str


@dataclass(frozen=True)
class Requirement:
    requirement: str
    status: str  # met | partial | missing
    evidence: str


@dataclass(frozen=True)
class Bug:
    description: str
    severity: str  # critical | major | minor
    location: str


@dataclass(frozen=True)
class ExplanationAssessment:
    accuracy: str
    completeness: str
    clarity: str
    feedback: str


@dataclass(frozen=True)
class AIReview:
    summary: str
    requirements: tuple[Requirement, ...]
    bugs: tuple[Bug, ...]
    explanation: ExplanationAssessment
    strengths: tuple[str, ...]
    improvements: tuple[str, ...]
    model: str
    files_reviewed: int = 0
    files_omitted: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReviewOutcome:
    status: ReviewStatus
    review: AIReview | None = None
    message: str | None = None


class Reviewer(Protocol):
    """Anything that can review a submission: Claude in production, a fake in tests."""

    @property
    def model(self) -> str: ...

    def review(self, task: str, explanation: str, sources: Sequence[SourceFile]) -> AIReview: ...


@dataclass(frozen=True)
class StaticCheck:
    """One name from the task or the explanation, looked up in the code without AI."""

    source: str  # task | explanation
    name: str
    status: str  # found | mismatch | missing
    detail: str


@dataclass(frozen=True)
class SubmissionReport:
    """A graded submission.

    ``overall_score`` and ``grade`` exist only when the AI review completed. Code quality alone
    says nothing about whether the task was solved, so it never earns a rank.
    """

    quality: ProjectReport
    outcome: ReviewOutcome
    task_score: int | None = None
    explanation_score: int | None = None
    overall_score: int | None = None
    grade: Grade | None = None
    checks: tuple[StaticCheck, ...] = ()
    weights: Mapping[str, int] = field(default_factory=lambda: dict(WEIGHTS))

    @property
    def verdict(self) -> str:
        """ "graded" for a full assignment grade, "quality_only" when the task wasn't verified."""
        return "graded" if self.grade is not None else "quality_only"

    @property
    def gate_score(self) -> int:
        """The score a pass/fail threshold applies to: overall when graded, else code quality."""
        return self.quality.quality_score if self.overall_score is None else self.overall_score


def grade_for(score: float) -> Grade:
    """Excellent from 90, Good from 70, Poor below."""
    if score >= EXCELLENT_MIN:
        return Grade.EXCELLENT
    if score >= GOOD_MIN:
        return Grade.GOOD
    return Grade.POOR


def task_score(review: AIReview) -> int:
    """Share of requirements met (partial counts half), minus a capped penalty for bugs."""
    if not review.requirements:
        return 0
    credit = sum(REQUIREMENT_CREDIT[item.status] for item in review.requirements)
    penalty = min(MAX_BUG_PENALTY, sum(BUG_PENALTY[bug.severity] for bug in review.bugs))
    return max(0, round_score(100 * credit / len(review.requirements)) - penalty)


def explanation_score(assessment: ExplanationAssessment) -> int:
    """Accuracy (50) + completeness (30) + clarity (20)."""
    return sum(
        EXPLANATION_POINTS[aspect][getattr(assessment, aspect)] for aspect in EXPLANATION_POINTS
    )


def run_review(
    reviewer: Reviewer | None, assignment: Assignment, sources: Sequence[SourceFile]
) -> ReviewOutcome:
    """Asks the reviewer, turning every failure into an outcome rather than an exception."""
    if reviewer is None:
        return ReviewOutcome(
            ReviewStatus.UNAVAILABLE,
            message="AI review isn't configured, so the task and explanation weren't verified.",
        )
    try:
        review = reviewer.review(assignment.task, assignment.explanation, sources)
        return ReviewOutcome(ReviewStatus.COMPLETED, review=review)
    except ReviewError as error:
        return ReviewOutcome(ReviewStatus.FAILED, message=str(error))


def grade_submission(
    quality: ProjectReport, outcome: ReviewOutcome, checks: tuple[StaticCheck, ...] = ()
) -> SubmissionReport:
    """Final grade: 50% task, 35% code quality, 15% explanation.

    Without a completed review there is no final grade, only the code-quality score.
    """
    review = outcome.review
    if outcome.status is not ReviewStatus.COMPLETED or review is None:
        return SubmissionReport(quality, outcome, checks=checks)

    task = task_score(review)
    explained = explanation_score(review.explanation)
    weighted = (
        WEIGHTS["task"] * task
        + WEIGHTS["quality"] * quality.quality_score
        + WEIGHTS["explanation"] * explained
    )
    overall = round_score(weighted / sum(WEIGHTS.values()))
    return SubmissionReport(
        quality, outcome, task, explained, overall, grade_for(overall), checks=checks
    )


def parse_review(
    payload: Any, *, model: str, files_reviewed: int, files_omitted: Sequence[str]
) -> AIReview:
    """Validates the reviewer's JSON answer and turns it into an :class:`AIReview`."""
    data = _mapping(payload, "review")
    explanation = _mapping(data.get("explanation"), "explanation")
    return AIReview(
        summary=_text(data.get("summary"), "summary"),
        requirements=tuple(_requirement(item) for item in _items(data.get("requirements"))),
        bugs=tuple(_bug(item) for item in _items(data.get("bugs"))),
        explanation=ExplanationAssessment(
            accuracy=_choice(explanation.get("accuracy"), EXPLANATION_POINTS["accuracy"]),
            completeness=_choice(
                explanation.get("completeness"), EXPLANATION_POINTS["completeness"]
            ),
            clarity=_choice(explanation.get("clarity"), EXPLANATION_POINTS["clarity"]),
            feedback=_text(explanation.get("feedback"), "explanation feedback"),
        ),
        strengths=tuple(_text(item, "strength") for item in _items(data.get("strengths"))),
        improvements=tuple(_text(item, "improvement") for item in _items(data.get("improvements"))),
        model=model,
        files_reviewed=files_reviewed,
        files_omitted=tuple(files_omitted),
    )


def _requirement(item: Any) -> Requirement:
    data = _mapping(item, "requirement")
    return Requirement(
        requirement=_text(data.get("requirement"), "requirement"),
        status=_choice(data.get("status"), REQUIREMENT_CREDIT),
        evidence=_text(data.get("evidence"), "evidence"),
    )


def _bug(item: Any) -> Bug:
    data = _mapping(item, "bug")
    return Bug(
        description=_text(data.get("description"), "bug description"),
        severity=_choice(data.get("severity"), BUG_PENALTY),
        location=_text(data.get("location"), "bug location"),
    )


def _mapping(value: Any, name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ReviewFormatError(f"The AI review is missing its {name} section.")
    return value


def _items(value: Any) -> list[Any]:
    if not isinstance(value, list):
        raise ReviewFormatError("The AI review has a malformed list.")
    return value[:MAX_LIST_ITEMS]


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str):
        raise ReviewFormatError(f"The AI review has no {name}.")
    return value.strip()


def _choice(value: Any, allowed: Mapping[str, Any]) -> str:
    if value not in allowed:
        raise ReviewFormatError(f"The AI review used an unknown rating: {value!r}.")
    return str(value)
