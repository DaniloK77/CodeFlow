from __future__ import annotations

import pytest

from api.quota import DailyQuota


def make_quota(per_client: int = 2, overall: int = 3) -> tuple[DailyQuota, list[float]]:
    now = [0.0]
    return DailyQuota(per_client, overall, window_seconds=100, clock=lambda: now[0]), now


def test_limits_each_client_and_frees_up_over_time() -> None:
    quota, now = make_quota()

    assert quota.acquire("ann") is None
    assert quota.acquire("ann") is None
    assert quota.acquire("ann") == pytest.approx(100)
    assert quota.remaining("ann") == 0

    now[0] = 100.5
    assert quota.acquire("ann") is None


def test_caps_the_whole_service() -> None:
    quota, _ = make_quota(per_client=5, overall=3)

    for visitor in ("ann", "bob", "cid"):
        assert quota.acquire(visitor) is None

    assert quota.acquire("dan") is not None
    assert quota.remaining("dan") == 0


def test_release_refunds_a_failed_review() -> None:
    quota, _ = make_quota()
    quota.acquire("ann")

    quota.release("ann")

    assert quota.remaining("ann") == 2
