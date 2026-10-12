import type { z } from "zod";

import type { SnippetLanguage } from "./constants";
import {
  type AnalysisReport,
  analysisReportSchema,
  errorBodySchema,
  type Health,
  healthSchema,
} from "./schema";

export class AnalyzerApiError extends Error {
  /** HTTP status, or `null` when the service could not be reached at all. */
  readonly status: number | null;
  readonly retryAfterSeconds: number | null;
  /** The grader's reason for refusing (`not_code`, `too_little_code`, …), when it gave one. */
  readonly code: string | null;

  constructor(
    message: string,
    status: number | null = null,
    retryAfterSeconds: number | null = null,
    code: string | null = null,
  ) {
    super(message);
    this.name = "AnalyzerApiError";
    this.status = status;
    this.retryAfterSeconds = retryAfterSeconds;
    this.code = code;
  }
}

/** What the student was asked to do and how they say they did it. */
export interface Assignment {
  task: string;
  explanation: string;
}

export interface SnippetPayload extends Assignment {
  code: string;
  language: SnippetLanguage;
  filename?: string;
}

export function reviewSnippet(payload: SnippetPayload, signal?: AbortSignal) {
  return request("/api/review/snippet", analysisReportSchema, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    signal: signal ?? null,
  });
}

export function reviewArchive(
  file: File,
  assignment: Assignment,
  signal?: AbortSignal,
): Promise<AnalysisReport> {
  const body = new FormData();
  body.append("task", assignment.task);
  body.append("explanation", assignment.explanation);
  body.append("file", file);
  return request("/api/review/archive", analysisReportSchema, {
    method: "POST",
    body,
    signal: signal ?? null,
  });
}

export function fetchHealth(signal?: AbortSignal): Promise<Health> {
  return request("/api/health", healthSchema, { signal: signal ?? null });
}

/** Absolute URL for an API path: `VITE_API_URL` in production, same origin (proxied) in dev. */
export function apiUrl(path: string): string {
  return new URL(path, apiBase()).toString();
}

function apiBase(): string {
  const configured = import.meta.env.VITE_API_URL?.trim();
  if (configured) return configured;
  return window.location.origin;
}

async function request<Schema extends z.ZodType>(
  path: string,
  schema: Schema,
  init: RequestInit,
): Promise<z.output<Schema>> {
  const response = await send(path, init);
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) throw toApiError(response, body);

  const parsed = schema.safeParse(body);
  if (!parsed.success) {
    throw new AnalyzerApiError("The grading service sent an unexpected response.", response.status);
  }
  return parsed.data;
}

async function send(path: string, init: RequestInit): Promise<Response> {
  try {
    return await fetch(apiUrl(path), init);
  } catch (error) {
    // Cancellation is not a failure: let the caller see the original AbortError.
    if (init.signal?.aborted) throw error;
    throw new AnalyzerApiError("The grading service is offline.");
  }
}

function toApiError(response: Response, body: unknown): AnalyzerApiError {
  const parsed = errorBodySchema.safeParse(body);
  let message = `The request failed (HTTP ${response.status}).`;
  if (parsed.success) {
    const { detail } = parsed.data;
    message = typeof detail === "string" ? detail : detail.map((item) => item.msg).join("; ");
  }
  const retryAfter = Number(response.headers.get("Retry-After"));
  const code = parsed.success ? (parsed.data.code ?? null) : null;
  return new AnalyzerApiError(message, response.status, retryAfter > 0 ? retryAfter : null, code);
}
