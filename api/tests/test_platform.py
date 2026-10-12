from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.analysis import AnalysisRunner, ServiceBusyError
from api.config import Settings
from api.main import create_app
from api.rate_limit import SlidingWindowRateLimiter

from .conftest import snippet


def test_health_reports_version_ai_status_and_limits(
    client: TestClient, client_without_ai: TestClient
) -> None:
    body = client.get("/api/health").json()

    assert body["status"] == "ok"
    assert body["limits"]["max_snippet_chars"] == 5_000
    assert body["limits"]["min_task_chars"] == 20
    assert body["ai_review"] == {
        "enabled": True,
        "model": "claude-test",
        "reviews_per_day": 5,
        "remaining_today": 5,
    }
    assert client_without_ai.get("/api/health").json()["ai_review"]["enabled"] is False


def test_openapi_contract_is_published(client: TestClient) -> None:
    paths = client.get("/api/openapi.json").json()["paths"]
    assert set(paths) == {"/api/health", "/api/review/snippet", "/api/review/archive"}


def test_cors_allows_only_configured_origins(client: TestClient) -> None:
    allowed = client.get("/api/health", headers={"Origin": "http://localhost:5173"})
    blocked = client.get("/api/health", headers={"Origin": "https://evil.example"})

    assert allowed.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert "access-control-allow-origin" not in blocked.headers


def test_rate_limit_returns_429_with_retry_after() -> None:
    client = TestClient(create_app(Settings(rate_limit_requests=2), reviewer_factory=lambda: None))
    payload = snippet()

    statuses = [client.post("/api/review/snippet", json=payload).status_code for _ in range(3)]

    assert statuses == [200, 200, 429]
    limited = client.post("/api/review/snippet", json=payload)
    assert int(limited.headers["retry-after"]) > 0


def test_sliding_window_frees_capacity_over_time() -> None:
    now = [0.0]
    limiter = SlidingWindowRateLimiter(limit=2, window_seconds=10, clock=lambda: now[0])

    assert limiter.hit("ip") is None
    assert limiter.hit("ip") is None
    assert limiter.hit("ip") == pytest.approx(10)
    assert limiter.hit("other-ip") is None

    now[0] = 10.5
    assert limiter.hit("ip") is None


def test_a_busy_grader_answers_503_with_retry_after() -> None:
    app = create_app(Settings(rate_limit_requests=100), reviewer_factory=lambda: None)
    app.state.analysis = AnalysisRunner(timeout=0.1, slots=0)  # every slot taken

    response = TestClient(app).post("/api/review/snippet", json=snippet())

    assert response.status_code == 503
    assert response.json()["code"] == "busy"
    assert response.headers["retry-after"] == "5"


def test_the_runner_refuses_work_when_no_slot_frees_up() -> None:
    with pytest.raises(ServiceBusyError):
        AnalysisRunner(timeout=0.1, slots=0).run(len, "abc")


def test_settings_from_environment() -> None:
    settings = Settings.from_env(
        {
            "CODEGRADE_ALLOWED_ORIGINS": "https://a.dev, https://b.dev",
            "CODEGRADE_RATE_LIMIT": "5",
            "CODEGRADE_AI_REVIEWS_PER_DAY": "3",
            "CODEGRADE_ANALYSIS_TIMEOUT": "2.5",
            "CODEGRADE_MAX_CONCURRENT_ANALYSES": "2",
        }
    )
    assert settings.analysis_timeout_seconds == 2.5
    assert settings.max_concurrent_analyses == 2
    assert settings.allowed_origins == ("https://a.dev", "https://b.dev")
    assert settings.rate_limit_requests == 5
    assert settings.ai_reviews_per_day == 3
