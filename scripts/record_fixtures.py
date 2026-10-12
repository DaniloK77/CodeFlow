"""Regenerates the web app's test fixtures from the real API code.

    npm run fixtures

Static analysis is real. Claude is replaced by a fixed, clearly labelled review, so the
fixtures are reproducible and recording them costs nothing.
"""

from __future__ import annotations

import io
import json
import sys
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from api.config import Settings
from api.main import create_app
from tools.codegrade.assignment import AIReview, Bug, ExplanationAssessment, Requirement
from tools.codegrade.tests.factories import FakeReviewer

ROOT = Path(__file__).resolve().parents[1]

FIXTURES = ROOT / "src" / "test" / "fixtures"
EXAMPLE_REPORTS = ROOT / "src" / "content" / "exampleReports.generated.json"

# A stand-in for Claude's review of the Todo list example (it misses the "tasks left" count).
TODO_REVIEW = AIReview(
    summary=(
        "Adding and completing tasks works, but the component never shows how many tasks "
        "are left, which the task asks for."
    ),
    requirements=(
        Requirement("Type a task and add it with a button", "met", "TodoList.jsx:7-10, 20"),
        Requirement("Mark a task as done by clicking it", "met", "TodoList.jsx:12-14, 23"),
        Requirement("Done tasks are crossed out", "partial", "TodoList.jsx:23 sets a class only"),
        Requirement("Show how many tasks are still left", "missing", "No count is rendered"),
    ),
    bugs=(Bug("Empty tasks can be added", "minor", "TodoList.jsx:7"),),
    explanation=ExplanationAssessment(
        "accurate", "partial", "clear", "Accurate, but it doesn't mention the missing count."
    ),
    strengths=("Immutable state updates", "Stable keys from ids"),
    improvements=(
        "Render the number of tasks that aren't done",
        "Use a <button> per task so it works with the keyboard",
    ),
    model="claude-opus-5-5 (stubbed)",
    files_reviewed=1,
)


def write(name: str, payload: dict) -> None:
    payload["duration_ms"] = 3.2  # keep fixtures stable between runs
    (FIXTURES / name).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {name}: {payload['verdict']} quality {payload['scores']['quality']}")


def main() -> None:
    """Grades every example (with and without a stubbed AI review) and writes the fixtures."""
    examples = json.load(sys.stdin)
    settings = Settings(rate_limit_requests=1_000, ai_reviews_per_day=1_000)
    without_ai = TestClient(create_app(settings, reviewer_factory=lambda: None))
    with_ai = TestClient(create_app(settings, reviewer_factory=lambda: FakeReviewer(TODO_REVIEW)))

    for example in examples:
        body = {key: example[key] for key in ("task", "explanation", "code", "language")}
        body["filename"] = example["fileName"]
        write(
            f"quality-{example['id']}.json",
            without_ai.post("/api/review/snippet", json=body).json(),
        )
        if example["id"] == "todo-list":
            write("review-todo-list.json", with_ai.post("/api/review/snippet", json=body).json())

    reports = {}
    for example in examples:
        body = {key: example[key] for key in ("task", "explanation", "code", "language")}
        body["filename"] = example["fileName"]
        report = without_ai.post("/api/review/snippet", json=body).json()
        reports[example["id"]] = {
            "quality": report["scores"]["quality"],
            "codeLines": report["quality"]["files"][0]["code_lines"],
            "findings": [
                {key: item[key] for key in ("rule", "severity", "line", "message")}
                for item in report["quality"]["files"][0]["findings"]
            ],
            "checks": report["checks"],
        }
    EXAMPLE_REPORTS.write_text(json.dumps(reports, indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {EXAMPLE_REPORTS.name}")

    # A request the grader turns down, for the web app's tests.
    rejected = without_ai.post("/api/review/snippet", json={**body, "code": "hello there " * 20})
    (FIXTURES / "rejected-not-code.json").write_text(json.dumps(rejected.json(), indent=2) + "\n")

    archive = io.BytesIO()
    with zipfile.ZipFile(archive, "w") as bundle:
        for example in examples:
            bundle.writestr(f"homework/src/{example['fileName']}", example["code"])
        bundle.writestr("homework/README.md", "# Homework\n")
    todo = next(example for example in examples if example["id"] == "todo-list")
    form = {"task": todo["task"], "explanation": todo["explanation"]}
    files = {"file": ("homework.zip", archive.getvalue(), "application/zip")}
    write(
        "archive-homework.json",
        without_ai.post("/api/review/archive", data=form, files=files).json(),
    )
    health = without_ai.get("/api/health").json()
    (FIXTURES / "health.json").write_text(json.dumps(health, indent=2) + "\n")


if __name__ == "__main__":
    main()
