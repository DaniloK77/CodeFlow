"""Request and response models. They double as the OpenAPI contract served at /api/docs."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

GradeName = Literal["Excellent", "Good", "Poor"]
SeverityName = Literal["error", "warning", "info"]
DimensionName = Literal[
    "reliability", "complexity", "readability", "documentation", "accessibility", "testing"
]
VerdictName = Literal["graded", "quality_only"]
ReviewStatusName = Literal["completed", "not_requested", "unavailable", "limited", "failed"]

# Mirrored by the web app's form validation (src/features/analyzer/constants.ts).
TASK_MIN_CHARS = 20
EXPLANATION_MIN_CHARS = 30
TEXT_MAX_CHARS = 10_000

TaskText = Field(
    min_length=TASK_MIN_CHARS,
    max_length=TEXT_MAX_CHARS,
    description="The assignment: what the code is supposed to do.",
)
ExplanationText = Field(
    min_length=EXPLANATION_MIN_CHARS,
    max_length=TEXT_MAX_CHARS,
    description="How the solution works, in the author's own words.",
)


class SnippetReviewRequest(BaseModel):
    task: str = TaskText
    explanation: str = ExplanationText
    code: str = Field(min_length=1, description="The solution's source code.")
    language: Literal["auto", "typescript", "tsx", "javascript", "jsx", "python"] = "auto"
    filename: str | None = Field(
        default=None,
        max_length=255,
        description="Optional original file name; its extension wins over `language`.",
    )


class Requirement(BaseModel):
    requirement: str
    status: Literal["met", "partial", "missing"]
    evidence: str


class Bug(BaseModel):
    description: str
    severity: Literal["critical", "major", "minor"]
    location: str


class ExplanationAssessment(BaseModel):
    accuracy: Literal["accurate", "partially_accurate", "inaccurate"]
    completeness: Literal["complete", "partial", "minimal"]
    clarity: Literal["clear", "understandable", "unclear"]
    feedback: str


class Review(BaseModel):
    status: ReviewStatusName
    message: str | None
    model: str | None
    summary: str | None
    requirements: list[Requirement]
    bugs: list[Bug]
    explanation: ExplanationAssessment | None
    strengths: list[str]
    improvements: list[str]
    files_reviewed: int
    files_omitted: list[str]


class Finding(BaseModel):
    rule: str
    severity: SeverityName
    dimension: DimensionName
    message: str
    path: str
    line: int


class FunctionMetrics(BaseModel):
    name: str
    start_line: int
    end_line: int
    complexity: int
    max_nesting: int
    params: int


class FileReport(BaseModel):
    path: str
    language: str
    code_lines: int
    functions: list[FunctionMetrics]
    findings: list[Finding]
    max_nesting: int
    duplicated_lines: int
    score: int
    points_lost: dict[DimensionName, float]
    longest_function: int
    max_complexity: int


class HygieneCheck(BaseModel):
    name: str
    passed: bool
    weight: int
    hint: str


class Quality(BaseModel):
    score: int
    code_score: int
    hygiene_score: int | None
    points_lost: dict[DimensionName, float]
    files: list[FileReport]
    hygiene: list[HygieneCheck]


class StaticCheck(BaseModel):
    """A name from the task or explanation, looked up in the code without AI."""

    source: Literal["task", "explanation"]
    name: str
    status: Literal["found", "mismatch", "missing"]
    detail: str


class Scores(BaseModel):
    task: int | None
    quality: int
    explanation: int | None


class Weights(BaseModel):
    task: int
    quality: int
    explanation: int


class SkippedFile(BaseModel):
    path: str
    reason: str


class ReviewResponse(BaseModel):
    tool: str
    version: str
    source: Literal["snippet", "archive"]
    name: str
    verdict: VerdictName = Field(
        description="`graded` when the AI review completed; otherwise `quality_only`."
    )
    grade: GradeName | None = Field(description="Only for a graded submission, never for quality.")
    overall_score: int | None = Field(description="Only for a graded submission.")
    weights: Weights
    scores: Scores
    review: Review
    checks: list[StaticCheck]
    quality: Quality
    skipped: list[SkippedFile] = Field(default_factory=list)
    duration_ms: float


class Limits(BaseModel):
    max_upload_bytes: int
    max_snippet_chars: int
    max_source_files: int
    rate_limit_requests: int
    rate_limit_window_seconds: float
    min_task_chars: int
    min_explanation_chars: int


class AIReviewInfo(BaseModel):
    enabled: bool
    model: str | None
    reviews_per_day: int
    remaining_today: int


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    ai_review: AIReviewInfo
    limits: Limits


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = Field(
        default=None,
        description=(
            "Machine-readable reason: `not_code`, `unsupported_language`, `too_little_code`, "
            "`analysis_timeout`, `invalid_archive`, `archive_too_large`, `busy`."
        ),
    )
