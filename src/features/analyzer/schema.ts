import { z } from "zod";

import type { GradeName } from "@/types/content";

import { DIMENSIONS } from "./dimensions";

// Runtime contract for the codegrade API (see api/schemas.py). Responses are validated at the
// boundary and mapped from snake_case DTOs to the camelCase model the UI works with.

export const GRADES = ["Excellent", "Good", "Poor"] as const satisfies readonly GradeName[];
export type Grade = (typeof GRADES)[number];

export const SEVERITIES = ["error", "warning", "info"] as const;
export type Severity = (typeof SEVERITIES)[number];

export { DIMENSIONS, type Dimension } from "./dimensions";

export const REVIEW_STATUSES = [
  "completed",
  "not_requested",
  "unavailable",
  "limited",
  "failed",
] as const;

export const VERDICTS = ["graded", "quality_only"] as const;

const checkSchema = z.object({
  source: z.enum(["task", "explanation"]),
  name: z.string(),
  status: z.enum(["found", "mismatch", "missing"]),
  detail: z.string(),
});

const findingSchema = z.object({
  rule: z.string(),
  severity: z.enum(SEVERITIES),
  dimension: z.enum(DIMENSIONS),
  message: z.string(),
  path: z.string(),
  line: z.number().int(),
});

const pointsLostSchema = z.record(z.enum(DIMENSIONS), z.number());

const fileReportSchema = z
  .object({
    path: z.string(),
    language: z.string(),
    code_lines: z.number(),
    findings: z.array(findingSchema),
    score: z.number(),
    max_complexity: z.number(),
  })
  .transform((file) => ({
    path: file.path,
    language: file.language,
    codeLines: file.code_lines,
    findings: file.findings,
    score: file.score,
    maxComplexity: file.max_complexity,
  }));

const reviewSchema = z
  .object({
    status: z.enum(REVIEW_STATUSES),
    message: z.string().nullable(),
    model: z.string().nullable(),
    summary: z.string().nullable(),
    requirements: z.array(
      z.object({
        requirement: z.string(),
        status: z.enum(["met", "partial", "missing"]),
        evidence: z.string(),
      }),
    ),
    bugs: z.array(
      z.object({
        description: z.string(),
        severity: z.enum(["critical", "major", "minor"]),
        location: z.string(),
      }),
    ),
    explanation: z
      .object({
        accuracy: z.enum(["accurate", "partially_accurate", "inaccurate"]),
        completeness: z.enum(["complete", "partial", "minimal"]),
        clarity: z.enum(["clear", "understandable", "unclear"]),
        feedback: z.string(),
      })
      .nullable(),
    strengths: z.array(z.string()),
    improvements: z.array(z.string()),
    files_omitted: z.array(z.string()),
  })
  .transform(({ files_omitted, ...review }) => ({ ...review, filesOmitted: files_omitted }));

export const analysisReportSchema = z
  .object({
    version: z.string(),
    source: z.enum(["snippet", "archive"]),
    name: z.string(),
    verdict: z.enum(VERDICTS),
    grade: z.enum(GRADES).nullable(),
    overall_score: z.number().nullable(),
    weights: z.object({ task: z.number(), quality: z.number(), explanation: z.number() }),
    scores: z.object({
      task: z.number().nullable(),
      quality: z.number(),
      explanation: z.number().nullable(),
    }),
    review: reviewSchema,
    checks: z.array(checkSchema),
    quality: z.object({
      score: z.number(),
      code_score: z.number(),
      hygiene_score: z.number().nullable(),
      points_lost: pointsLostSchema,
      files: z.array(fileReportSchema),
      hygiene: z.array(
        z.object({ name: z.string(), passed: z.boolean(), weight: z.number(), hint: z.string() }),
      ),
    }),
    skipped: z.array(z.object({ path: z.string(), reason: z.string() })),
    duration_ms: z.number(),
  })
  .transform((report) => ({
    version: report.version,
    source: report.source,
    name: report.name,
    verdict: report.verdict,
    grade: report.grade,
    overallScore: report.overall_score,
    weights: report.weights,
    scores: report.scores,
    review: report.review,
    checks: report.checks,
    quality: {
      score: report.quality.score,
      codeScore: report.quality.code_score,
      hygieneScore: report.quality.hygiene_score,
      pointsLost: report.quality.points_lost,
      files: report.quality.files,
      hygiene: report.quality.hygiene,
    },
    skipped: report.skipped,
    durationMs: report.duration_ms,
  }));

export const healthSchema = z.object({
  status: z.literal("ok"),
  version: z.string(),
  ai_review: z.object({
    enabled: z.boolean(),
    model: z.string().nullable(),
    reviews_per_day: z.number(),
    remaining_today: z.number(),
  }),
});

/**
 * FastAPI returns `detail` as a string, or as a list of validation errors. Errors raised by the
 * grader itself also carry a machine-readable `code` (see ErrorResponse in api/schemas.py).
 */
export const errorBodySchema = z.object({
  detail: z.union([z.string(), z.array(z.object({ msg: z.string() }))]),
  code: z.string().nullish(),
});

export type AnalysisReport = z.output<typeof analysisReportSchema>;
export type AssignmentReview = AnalysisReport["review"];
export type FileReport = AnalysisReport["quality"]["files"][number];
export type Finding = FileReport["findings"][number];
export type StaticCheck = AnalysisReport["checks"][number];
export type Health = z.output<typeof healthSchema>;
