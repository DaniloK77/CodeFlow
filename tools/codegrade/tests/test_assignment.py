import unittest

from tools.codegrade.analyzer import build_report
from tools.codegrade.assignment import (
    Assignment,
    ReviewError,
    ReviewFormatError,
    ReviewOutcome,
    ReviewStatus,
    explanation_score,
    grade_submission,
    parse_review,
    run_review,
    task_score,
)
from tools.codegrade.models import Grade

from .factories import FakeReviewer, make_review
from .helpers import make_source

CLEAN = '''
def total(prices: list[float]) -> float:
    """Sum of all prices."""
    return sum(prices)


def test_total() -> None:
    assert total([1.0, 2.0]) == 3.0
'''
ASSIGNMENT = Assignment(task="Sum a list of prices.", explanation="I use sum() on the list.")


def quality_report():
    return build_report([make_source(CLEAN, "total.py")], None, root_label="total.py")


class TaskScoreTest(unittest.TestCase):
    def test_partial_requirements_earn_half_credit(self) -> None:
        self.assertEqual(task_score(make_review(["met", "partial", "missing", "met"])), 63)

    def test_bugs_cost_points_up_to_a_cap(self) -> None:
        self.assertEqual(task_score(make_review(["met"], bugs=["major", "minor"])), 84)
        self.assertEqual(task_score(make_review(["met"], bugs=["critical"] * 5)), 50)

    def test_no_requirements_means_no_credit(self) -> None:
        self.assertEqual(task_score(make_review([])), 0)


class ExplanationScoreTest(unittest.TestCase):
    def test_rates_accuracy_completeness_and_clarity(self) -> None:
        best = make_review(explanation=("accurate", "complete", "clear")).explanation
        middle = make_review(explanation=("partially_accurate", "partial", "understandable"))
        worst = make_review(explanation=("inaccurate", "minimal", "unclear")).explanation

        self.assertEqual(explanation_score(best), 100)
        self.assertEqual(explanation_score(middle.explanation), 52)
        self.assertEqual(explanation_score(worst), 0)


class GradeSubmissionTest(unittest.TestCase):
    def test_weights_task_quality_and_explanation(self) -> None:
        review = make_review(["met", "missing"], explanation=("accurate", "partial", "clear"))
        outcome = ReviewOutcome(ReviewStatus.COMPLETED, review=review)

        report = grade_submission(quality_report(), outcome)

        # task 50, quality 100, explanation 85 → (50·50 + 35·100 + 15·85) / 100
        self.assertEqual((report.task_score, report.explanation_score), (50, 85))
        self.assertEqual(report.overall_score, 73)
        self.assertIs(report.grade, Grade.GOOD)
        self.assertEqual(report.verdict, "graded")
        self.assertEqual(report.gate_score, 73)

    def test_without_a_review_only_quality_counts(self) -> None:
        outcome = ReviewOutcome(ReviewStatus.UNAVAILABLE, message="not configured")

        report = grade_submission(quality_report(), outcome)

        self.assertIsNone(report.task_score)
        self.assertIsNone(report.overall_score)
        self.assertIsNone(report.grade)  # code quality alone never earns a rank
        self.assertEqual(report.verdict, "quality_only")
        self.assertEqual(report.gate_score, report.quality.quality_score)


class RunReviewTest(unittest.TestCase):
    def test_passes_the_assignment_and_sources_to_the_reviewer(self) -> None:
        reviewer = FakeReviewer()

        outcome = run_review(reviewer, ASSIGNMENT, [make_source(CLEAN, "total.py")])

        self.assertIs(outcome.status, ReviewStatus.COMPLETED)
        self.assertEqual(reviewer.calls, [(ASSIGNMENT.task, ASSIGNMENT.explanation, ["total.py"])])

    def test_turns_failures_into_outcomes(self) -> None:
        self.assertIs(run_review(None, ASSIGNMENT, []).status, ReviewStatus.UNAVAILABLE)
        failing = FakeReviewer(result=ReviewError("The AI reviewer is busy."))
        outcome = run_review(failing, ASSIGNMENT, [])
        self.assertEqual(
            (outcome.status, outcome.message), (ReviewStatus.FAILED, "The AI reviewer is busy.")
        )


PAYLOAD = {
    "summary": "Works.",
    "requirements": [{"requirement": "Sums prices", "status": "met", "evidence": "total.py:3"}],
    "bugs": [],
    "explanation": {
        "accuracy": "accurate",
        "completeness": "complete",
        "clarity": "clear",
        "feedback": "Good.",
    },
    "strengths": ["Short"],
    "improvements": [],
}


class ParseReviewTest(unittest.TestCase):
    def test_builds_a_review_from_valid_json(self) -> None:
        review = parse_review(PAYLOAD, model="m", files_reviewed=1, files_omitted=["big.py"])

        self.assertEqual(review.requirements[0].status, "met")
        self.assertEqual(review.files_omitted, ("big.py",))

    def test_rejects_unknown_ratings_and_missing_sections(self) -> None:
        bad_rating = {
            **PAYLOAD,
            "requirements": [{**PAYLOAD["requirements"][0], "status": "done"}],
        }
        with self.assertRaises(ReviewFormatError):
            parse_review(bad_rating, model="m", files_reviewed=1, files_omitted=[])
        with self.assertRaises(ReviewFormatError):
            parse_review({"summary": "x"}, model="m", files_reviewed=1, files_omitted=[])
