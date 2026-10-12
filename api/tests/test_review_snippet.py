from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.config import Settings
from api.main import create_app
from tools.codegrade.assignment import ReviewError
from tools.codegrade.tests.factories import FakeReviewer

from .conftest import EXPLANATION, MESSY_COMPONENT, TASK, snippet

ENGLISH = "I think this is a really good solution, please grade my homework kindly. " * 3
JAVA = """\
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello");
    }
}
"""
SQL = "SELECT name, email FROM users WHERE active = 1 ORDER BY name;\nSELECT 1 FROM dual;\n"
ONE_LINER = "const total = 5;"


def review(client: TestClient, **payload: object) -> dict:
    response = client.post("/api/review/snippet", json=snippet(**payload))
    assert response.status_code == 200, response.text
    return response.json()


def test_combines_task_quality_and_explanation(client: TestClient, reviewer: FakeReviewer) -> None:
    report = review(client)

    # requirements met, met, partial → task 83; quality 93 (no tests); explanation 100
    assert report["scores"] == {"task": 83, "quality": 93, "explanation": 100}
    assert report["weights"] == {"task": 50, "quality": 35, "explanation": 15}
    assert report["overall_score"] == 89
    assert report["grade"] == "Good"
    assert report["verdict"] == "graded"
    assert report["review"]["status"] == "completed"
    assert reviewer.calls == [(TASK, EXPLANATION, ["snippet.tsx"])]


def test_names_from_the_explanation_are_checked_against_the_code(client: TestClient) -> None:
    report = review(client)

    assert report["checks"] == [
        {
            "source": "explanation",
            "name": "name",
            "status": "found",
            "detail": "appears in the code",
        }
    ]


def test_static_findings_lower_the_quality_score(client: TestClient) -> None:
    report = review(client, code=MESSY_COMPONENT, filename="List.jsx")

    rules = {finding["rule"] for finding in report["quality"]["files"][0]["findings"]}
    assert {"no-var", "no-debugger", "index-as-key", "img-alt", "button-type", "no-tests"} <= rules
    assert report["scores"]["quality"] < 40
    lost = sum(report["quality"]["points_lost"].values())
    assert lost == pytest.approx(100 - report["scores"]["quality"], abs=0.3)


def test_without_ai_there_is_a_score_but_no_rank(client_without_ai: TestClient) -> None:
    report = review(client_without_ai)

    assert report["verdict"] == "quality_only"
    assert report["grade"] is None
    assert report["overall_score"] is None
    assert report["review"]["status"] == "unavailable"
    assert report["scores"]["task"] is None
    assert report["scores"]["quality"] == 93


def test_a_failed_review_is_reported_and_not_counted(
    client: TestClient, reviewer: FakeReviewer
) -> None:
    reviewer.result = ReviewError("The AI reviewer is busy. Please try again in a minute.")

    report = review(client)

    assert report["verdict"] == "quality_only"
    assert report["grade"] is None
    assert report["review"] == {
        **report["review"],
        "status": "failed",
        "message": "The AI reviewer is busy. Please try again in a minute.",
    }
    health = client.get("/api/health").json()
    assert health["ai_review"]["remaining_today"] == health["ai_review"]["reviews_per_day"]


def test_daily_ai_allowance(client: TestClient, settings, reviewer: FakeReviewer) -> None:
    statuses = [review(client)["review"]["status"] for _ in range(settings.ai_reviews_per_day + 1)]

    assert statuses[:-1] == ["completed"] * settings.ai_reviews_per_day
    assert statuses[-1] == "limited"
    assert len(reviewer.calls) == settings.ai_reviews_per_day


@pytest.mark.parametrize(
    ("code", "reason"),
    [
        (ENGLISH, "not_code"),
        ("asdf qwer zxcv 1234 !!! ??? lorem ipsum", "not_code"),
        (JAVA, "unsupported_language"),
        (SQL, "unsupported_language"),
        (ONE_LINER, "too_little_code"),
    ],
    ids=["english", "garbage", "java", "sql", "one-liner"],
)
def test_input_that_is_not_gradable_code_is_rejected_before_any_ai_call(
    client: TestClient, reviewer: FakeReviewer, code: str, reason: str
) -> None:
    response = client.post("/api/review/snippet", json=snippet(code))

    assert response.status_code == 422
    assert response.json()["code"] == reason
    assert reviewer.calls == []  # the AI was never asked, and no allowance was used
    health = client.get("/api/health").json()
    assert health["ai_review"]["remaining_today"] == health["ai_review"]["reviews_per_day"]


def test_a_file_name_cannot_make_other_languages_gradable(client: TestClient) -> None:
    response = client.post("/api/review/snippet", json=snippet(JAVA, filename="Main.js"))

    assert response.status_code == 422
    assert response.json()["code"] == "unsupported_language"


def test_broken_code_is_graded_and_capped_not_rejected(client_without_ai: TestClient) -> None:
    broken = "function add(a, b {\n  return a + ;\n}\nconst total = add(1, 2);\nrun(total)\n"

    report = review(client_without_ai, code=broken, language="javascript")

    rules = {finding["rule"] for finding in report["quality"]["files"][0]["findings"]}
    assert "syntax-error" in rules
    assert report["scores"]["quality"] <= 40


def test_pathological_code_times_out_instead_of_hanging() -> None:
    settings = Settings(
        max_snippet_chars=300_000, analysis_timeout_seconds=1.5, rate_limit_requests=100
    )
    client = TestClient(create_app(settings, reviewer_factory=lambda: None))

    response = client.post("/api/review/snippet", json=snippet('"' * 300_000, filename="evil.ts"))

    assert response.status_code == 422
    assert response.json()["code"] == "analysis_timeout"


def test_validates_the_assignment_fields(client: TestClient) -> None:
    too_short = client.post("/api/review/snippet", json=snippet(task="Do it"))
    no_explanation = client.post("/api/review/snippet", json={"task": TASK, "code": "x"})
    too_long = client.post("/api/review/snippet", json=snippet(code="x" * 5_001))

    assert too_short.status_code == 422
    assert no_explanation.status_code == 422
    assert too_long.status_code == 413
    assert "5,000" in too_long.json()["detail"]


def test_detects_python_and_respects_file_names(client: TestClient) -> None:
    python = "def add(a: int, b: int) -> int:\n    return a + b\n\n\nclass Calc:\n    pass\n"
    typed = "const a: number = 1;\nconst b: number = 2;\nexport const total = a + b;\n"

    assert review(client, code=python)["quality"]["files"][0]["language"] == "python"
    assert review(client, code=typed, language="typescript")["name"] == "snippet.ts"
    assert review(client, code=typed, filename="src/Card.tsx")["name"] == "Card.tsx"
    assert review(client, code=typed)["name"] == "snippet.ts"  # detected
