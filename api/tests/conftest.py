from __future__ import annotations

import io
import zipfile
from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient

from api.config import MB, Settings
from api.main import create_app
from tools.codegrade.tests.factories import FakeReviewer, make_review

TASK = "Write a TypeScript component that greets the user by name."
EXPLANATION = "The component takes a `name` prop and renders it inside a paragraph."

CLEAN_COMPONENT = """\
interface GreetingProps {
  name: string;
}

export function Greeting({ name }: GreetingProps) {
  return <p className="greeting">Hello, {name}</p>;
}
"""

MESSY_COMPONENT = """\
var items = [];
export default function List() {
  console.log(items);
  debugger;
  return items.map((item, i) => (
    <li key={i}>
      <img src={item} />
      <button onClick={() => remove(i)}>x</button>
      <a href="#">more</a>
    </li>
  ));
}
"""


@pytest.fixture
def settings() -> Settings:
    return Settings(max_upload_bytes=1 * MB, max_snippet_chars=5_000, rate_limit_requests=100)


@pytest.fixture
def reviewer() -> FakeReviewer:
    return FakeReviewer(result=make_review(["met", "met", "partial"]))


@pytest.fixture
def client(settings: Settings, reviewer: FakeReviewer) -> TestClient:
    return TestClient(create_app(settings, reviewer_factory=lambda: reviewer))


@pytest.fixture
def client_without_ai(settings: Settings) -> TestClient:
    return TestClient(create_app(settings, reviewer_factory=lambda: None))


@pytest.fixture
def make_zip() -> Callable[[dict[str, str]], bytes]:
    def build(files: dict[str, str]) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for name, content in files.items():
                archive.writestr(name, content)
        return buffer.getvalue()

    return build


def snippet(code: str = CLEAN_COMPONENT, **extra: object) -> dict[str, object]:
    """A valid /api/review/snippet body."""
    return {"task": TASK, "explanation": EXPLANATION, "code": code, **extra}
