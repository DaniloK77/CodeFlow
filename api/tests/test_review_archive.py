from __future__ import annotations

from collections.abc import Callable

from fastapi.testclient import TestClient

from api.config import MB
from tools.codegrade.tests.factories import FakeReviewer

from .conftest import CLEAN_COMPONENT, EXPLANATION, MESSY_COMPONENT, TASK

ZipBuilder = Callable[[dict[str, str]], bytes]


def upload(client: TestClient, data: bytes, name: str = "project.zip", **form: str):
    fields = {"task": TASK, "explanation": EXPLANATION, **form}
    return client.post(
        "/api/review/archive", data=fields, files={"file": (name, data, "application/zip")}
    )


def test_grades_a_project_with_hygiene_and_review(
    client: TestClient, make_zip: ZipBuilder, reviewer: FakeReviewer
) -> None:
    data = make_zip(
        {
            "app-main/src/Greeting.tsx": CLEAN_COMPONENT,
            "app-main/src/List.jsx": MESSY_COMPONENT,
            "app-main/tsconfig.json": "{}",
            "app-main/node_modules/lib/index.js": "var ignored = true;",
        }
    )

    response = upload(client, data)

    assert response.status_code == 200, response.text
    report = response.json()
    assert report["source"] == "archive"
    assert report["name"] == "project.zip"
    paths = [item["path"] for item in report["quality"]["files"]]
    assert paths == ["src/Greeting.tsx", "src/List.jsx"]
    assert report["quality"]["hygiene_score"] == 10  # only static typing is in place
    assert reviewer.calls[0][2] == ["src/Greeting.tsx", "src/List.jsx"]


def test_lists_rejected_members(client: TestClient, make_zip: ZipBuilder) -> None:
    data = make_zip({"src/Greeting.tsx": CLEAN_COMPONENT, "../escape.js": "debugger;"})

    report = upload(client, data).json()

    assert report["skipped"] == [
        {"path": "../escape.js", "reason": "unsafe path (absolute or contains '..')"}
    ]


def test_rejects_bad_uploads(client: TestClient, make_zip: ZipBuilder) -> None:
    assert upload(client, b"plain text", name="notes.txt").status_code == 422
    corrupt = upload(client, b"not really a zip")
    assert corrupt.status_code == 422
    assert "not a valid .zip" in corrupt.json()["detail"]
    assert upload(client, make_zip({"README.md": "# hi"})).status_code == 422
    assert upload(client, make_zip({"a.py": "x = 1"}), task="short").status_code == 422


def test_rejects_uploads_over_the_size_limit(client: TestClient) -> None:
    response = upload(client, b"0" * (2 * MB))

    assert response.status_code == 413
    assert response.json()["detail"] == "upload exceeds the 1 MB limit"
