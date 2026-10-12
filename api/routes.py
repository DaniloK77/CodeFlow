"""HTTP endpoints. Grading is CPU- and network-bound, so it always runs in the worker pool."""

from __future__ import annotations

import math
from typing import Annotated, Any

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    Response,
    UploadFile,
    status,
)
from starlette.concurrency import run_in_threadpool

from tools.codegrade import __version__
from tools.codegrade.assignment import Assignment

from . import service
from .config import Settings
from .rate_limit import SlidingWindowRateLimiter
from .schemas import (
    EXPLANATION_MIN_CHARS,
    TASK_MIN_CHARS,
    TEXT_MAX_CHARS,
    AIReviewInfo,
    ErrorResponse,
    HealthResponse,
    Limits,
    ReviewResponse,
    SnippetReviewRequest,
)

router = APIRouter(prefix="/api")

_ERRORS: dict[int | str, dict[str, Any]] = {
    status.HTTP_413_CONTENT_TOO_LARGE: {"model": ErrorResponse},
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ErrorResponse},
    status.HTTP_429_TOO_MANY_REQUESTS: {"model": ErrorResponse},
    status.HTTP_503_SERVICE_UNAVAILABLE: {"model": ErrorResponse},
}


def client_id(request: Request) -> str:
    """The caller's address, used for rate limits and the daily AI allowance."""
    return request.client.host if request.client else "anonymous"


def get_settings(request: Request) -> Settings:
    """Settings the app was created with."""
    return request.app.state.settings


def review_context(request: Request) -> service.ReviewContext:
    """Reviewer and AI allowance for this caller."""
    state = request.app.state
    return service.ReviewContext(state.reviewer, state.ai_quota, client_id(request), state.analysis)


def enforce_rate_limit(request: Request, response: Response) -> None:
    """Rejects bursts with 429 + Retry-After, separately from the daily AI allowance."""
    limiter: SlidingWindowRateLimiter = request.app.state.rate_limiter
    retry_after = limiter.hit(client_id(request))
    if retry_after is not None:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests. Please wait a moment and try again.",
            headers={"Retry-After": str(math.ceil(retry_after))},
        )
    response.headers["X-RateLimit-Limit"] = str(limiter.limit)


SettingsDep = Annotated[Settings, Depends(get_settings)]
ContextDep = Annotated[service.ReviewContext, Depends(review_context)]
RateLimited = Depends(enforce_rate_limit)


@router.get("/health", response_model=HealthResponse, tags=["meta"])
def health(request: Request, settings: SettingsDep) -> HealthResponse:
    """Service status, whether AI review is available, and the free-plan limits."""
    reviewer = request.app.state.reviewer
    ai_review = AIReviewInfo(
        enabled=reviewer is not None,
        model=reviewer.model if reviewer is not None else None,
        reviews_per_day=settings.ai_reviews_per_day,
        remaining_today=request.app.state.ai_quota.remaining(client_id(request)),
    )
    limits = Limits(
        max_upload_bytes=settings.max_upload_bytes,
        max_snippet_chars=settings.max_snippet_chars,
        max_source_files=settings.archive_limits.max_source_files,
        rate_limit_requests=settings.rate_limit_requests,
        rate_limit_window_seconds=settings.rate_limit_window_seconds,
        min_task_chars=TASK_MIN_CHARS,
        min_explanation_chars=EXPLANATION_MIN_CHARS,
    )
    return HealthResponse(status="ok", version=__version__, ai_review=ai_review, limits=limits)


@router.post(
    "/review/snippet",
    response_model=ReviewResponse,
    responses=_ERRORS,
    dependencies=[RateLimited],
    tags=["review"],
    summary="Grade pasted code or one file against its task and explanation",
)
async def review_snippet(
    payload: SnippetReviewRequest, settings: SettingsDep, context: ContextDep
) -> dict[str, Any]:
    """Task fit (AI) 50% · code quality 35% · explanation (AI) 15%.

    Without a completed AI review there is no rank: the response is `quality_only`.
    Text that isn't code in a supported language is rejected with a 422 and a `code`.
    """
    if len(payload.code) > settings.max_snippet_chars:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail=f"code exceeds {settings.max_snippet_chars:,} characters",
        )
    return await run_in_threadpool(service.review_snippet, payload, context)


@router.post(
    "/review/archive",
    response_model=ReviewResponse,
    responses=_ERRORS,
    dependencies=[RateLimited],
    tags=["review"],
    summary="Grade a zipped project against its task and explanation",
)
async def review_archive(
    settings: SettingsDep,
    context: ContextDep,
    file: Annotated[UploadFile, File(description=".zip archive of the project")],
    task: Annotated[str, Form(min_length=TASK_MIN_CHARS, max_length=TEXT_MAX_CHARS)],
    explanation: Annotated[str, Form(min_length=EXPLANATION_MIN_CHARS, max_length=TEXT_MAX_CHARS)],
) -> dict[str, Any]:
    """Like /review/snippet, plus project hygiene (README, tests, CI, …) in code quality."""
    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="please upload a .zip file"
        )
    data = await file.read(settings.max_upload_bytes + 1)
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE, detail="archive is too large"
        )
    upload = service.ArchiveUpload(data, file.filename or "upload.zip", settings.archive_limits)
    assignment = Assignment(task, explanation)
    return await run_in_threadpool(service.review_archive, upload, assignment, context)
