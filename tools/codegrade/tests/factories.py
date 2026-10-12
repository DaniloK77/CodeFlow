"""Ready-made reviews and a fake reviewer for tests that don't call Claude."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from tools.codegrade.assignment import (
    AIReview,
    Bug,
    ExplanationAssessment,
    Requirement,
    ReviewError,
)
from tools.codegrade.source import SourceFile


def make_review(
    statuses: Sequence[str] = ("met", "met"),
    bugs: Sequence[str] = (),
    explanation: tuple[str, str, str] = ("accurate", "complete", "clear"),
) -> AIReview:
    """A review with one requirement per status and one bug per severity given."""
    return AIReview(
        summary="Solid work.",
        requirements=tuple(
            Requirement(f"requirement {index}", status, "main.py:1")
            for index, status in enumerate(statuses, 1)
        ),
        bugs=tuple(Bug(f"{severity} bug", severity, "main.py:2") for severity in bugs),
        explanation=ExplanationAssessment(*explanation, feedback="Clear write-up."),
        strengths=("Readable",),
        improvements=("Add tests",),
        model="claude-test",
        files_reviewed=1,
    )


@dataclass
class FakeReviewer:
    """Returns a canned review (or raises) and records what it was asked."""

    result: AIReview | ReviewError = field(default_factory=make_review)
    calls: list[tuple[str, str, list[str]]] = field(default_factory=list)
    model: str = "claude-test"

    def review(self, task: str, explanation: str, sources: Sequence[SourceFile]) -> AIReview:
        """The canned review, after recording the call."""
        self.calls.append((task, explanation, [source.label for source in sources]))
        if isinstance(self.result, ReviewError):
            raise self.result
        return self.result
