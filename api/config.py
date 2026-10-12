"""Runtime configuration, read once from ``CODEGRADE_*`` environment variables."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field

from tools.codegrade.archive import ArchiveLimits

MB = 1024 * 1024


@dataclass(frozen=True)
class Settings:
    max_upload_bytes: int = 5 * MB
    max_snippet_chars: int = 200_000
    rate_limit_requests: int = 20
    rate_limit_window_seconds: float = 60.0
    # Free plan: AI reviews per visitor per day, and for the whole service (cost ceiling).
    ai_reviews_per_day: int = 5
    ai_daily_budget: int = 200
    # Analysis runs in killable worker processes: how long one may take, and how many may run.
    analysis_timeout_seconds: float = 20.0
    max_concurrent_analyses: int = 4
    allowed_origins: tuple[str, ...] = ("http://localhost:5173", "http://127.0.0.1:5173")
    archive_limits: ArchiveLimits = field(
        default_factory=lambda: ArchiveLimits(max_source_files=400, max_total_bytes=10 * MB)
    )

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Defaults, overridden by any ``CODEGRADE_*`` variables that are set."""
        env = os.environ if env is None else env
        defaults = cls()

        def number(name: str, default: int) -> int:
            return int(env.get(name, default))

        origins = env.get("CODEGRADE_ALLOWED_ORIGINS")
        return cls(
            max_upload_bytes=number("CODEGRADE_MAX_UPLOAD_MB", 5) * MB,
            max_snippet_chars=number("CODEGRADE_MAX_SNIPPET_CHARS", defaults.max_snippet_chars),
            rate_limit_requests=number("CODEGRADE_RATE_LIMIT", defaults.rate_limit_requests),
            ai_reviews_per_day=number("CODEGRADE_AI_REVIEWS_PER_DAY", defaults.ai_reviews_per_day),
            ai_daily_budget=number("CODEGRADE_AI_DAILY_BUDGET", defaults.ai_daily_budget),
            analysis_timeout_seconds=float(
                env.get("CODEGRADE_ANALYSIS_TIMEOUT", defaults.analysis_timeout_seconds)
            ),
            max_concurrent_analyses=number(
                "CODEGRADE_MAX_CONCURRENT_ANALYSES", defaults.max_concurrent_analyses
            ),
            allowed_origins=(
                tuple(origin.strip() for origin in origins.split(",") if origin.strip())
                if origins
                else defaults.allowed_origins
            ),
        )
