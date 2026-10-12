"""Application factory.

Run locally from the repository root::

    python -m uvicorn api.main:app --reload --port 8000

Interactive OpenAPI docs are then served at http://localhost:8000/api/docs.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from tools.codegrade import __version__
from tools.codegrade.ai_review import reviewer_from_env
from tools.codegrade.archive import ArchiveError, ArchiveTooLargeError
from tools.codegrade.assignment import Reviewer
from tools.codegrade.isolation import AnalysisCrashedError, AnalysisTimeoutError
from tools.codegrade.languages import UngradableInputError

from .analysis import AnalysisRunner, ServiceBusyError
from .config import MB, Settings
from .middleware import BodySizeLimitMiddleware
from .quota import DailyQuota
from .rate_limit import SlidingWindowRateLimiter
from .routes import router

logger = logging.getLogger("codegrade.api")

# Multipart framing adds a little on top of the file itself.
_MULTIPART_OVERHEAD_BYTES = 64 * 1024


def create_app(
    settings: Settings | None = None,
    reviewer_factory: Callable[[], Reviewer | None] = reviewer_from_env,
) -> FastAPI:
    """Builds the API. Tests pass their own settings and a fake reviewer."""
    settings = settings or Settings.from_env()
    app = FastAPI(
        title="codegrade API",
        version=__version__,
        description=(
            "Grades a programming assignment as Excellent, Good or Poor: task fit (AI review, "
            "50%), code quality (static analysis, 35%) and the author's explanation (AI, 15%). "
            "Without an AI review only code quality is scored, and no rank is given."
        ),
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    app.state.settings = settings
    app.state.rate_limiter = SlidingWindowRateLimiter(
        settings.rate_limit_requests, settings.rate_limit_window_seconds
    )
    app.state.reviewer = reviewer_factory()
    app.state.analysis = AnalysisRunner(
        settings.analysis_timeout_seconds, settings.max_concurrent_analyses
    )
    app.state.ai_quota = DailyQuota(settings.ai_reviews_per_day, settings.ai_daily_budget)
    if app.state.reviewer is None:
        logger.warning("AI review is off: set ANTHROPIC_API_KEY to grade task fit and explanations")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.allowed_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        expose_headers=["Retry-After"],
    )
    app.add_middleware(
        BodySizeLimitMiddleware,
        max_body_bytes=settings.max_upload_bytes + _MULTIPART_OVERHEAD_BYTES,
        limit_label=f"{settings.max_upload_bytes / MB:g} MB",
    )
    app.add_exception_handler(ArchiveError, _archive_error_handler)
    app.add_exception_handler(UngradableInputError, _ungradable_handler)
    app.add_exception_handler(AnalysisTimeoutError, _timeout_handler)
    app.add_exception_handler(AnalysisCrashedError, _crash_handler)
    app.add_exception_handler(ServiceBusyError, _busy_handler)
    app.include_router(router)
    return app


def _error(status_code: int, detail: str, code: str, **headers: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code, content={"detail": detail, "code": code}, headers=headers
    )


async def _archive_error_handler(_request: Request, error: Exception) -> JSONResponse:
    too_large = isinstance(error, ArchiveTooLargeError)
    status_code = (
        status.HTTP_413_CONTENT_TOO_LARGE if too_large else status.HTTP_422_UNPROCESSABLE_CONTENT
    )
    logger.info("rejected archive: %s", error)
    return _error(status_code, str(error), "archive_too_large" if too_large else "invalid_archive")


async def _ungradable_handler(_request: Request, error: Exception) -> JSONResponse:
    code = error.code if isinstance(error, UngradableInputError) else "not_code"
    logger.info("ungradable input (%s): %s", code, error)
    return _error(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error), code)


async def _timeout_handler(_request: Request, error: Exception) -> JSONResponse:
    logger.warning("analysis timed out: %s", error)
    detail = "This code is too large or too tangled to analyse in time. Try a smaller piece."
    return _error(status.HTTP_422_UNPROCESSABLE_CONTENT, detail, "analysis_timeout")


async def _crash_handler(_request: Request, error: Exception) -> JSONResponse:
    logger.error("analysis worker failed: %s", error)
    detail = "The grader hit an unexpected problem with this submission."
    return _error(status.HTTP_500_INTERNAL_SERVER_ERROR, detail, "analysis_failed")


async def _busy_handler(_request: Request, error: Exception) -> JSONResponse:
    return _error(status.HTTP_503_SERVICE_UNAVAILABLE, str(error), "busy", **{"Retry-After": "5"})


app = create_app()
