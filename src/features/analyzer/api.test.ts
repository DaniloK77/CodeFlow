import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { fixtures, server } from "@/test/server";

import { AnalyzerApiError, apiUrl, reviewSnippet } from "./api";

const payload = {
  task: "Declare a constant named a.",
  explanation: "A single const declaration.",
  code: "const a = 1;",
  language: "auto",
} as const;

async function captureError(): Promise<AnalyzerApiError> {
  try {
    await reviewSnippet(payload);
  } catch (error) {
    if (error instanceof AnalyzerApiError) return error;
    throw error;
  }
  throw new Error("expected the request to fail");
}

describe("analyzer API client", () => {
  it("resolves API paths against the current origin by default", () => {
    expect(apiUrl("/api/health")).toBe(`${window.location.origin}/api/health`);
  });

  it("maps a validated response to the camelCase report model", async () => {
    const report = await reviewSnippet(payload);

    expect(report).toMatchObject({ verdict: "quality_only", grade: null, overallScore: null });
    expect(report.quality.score).toBeGreaterThan(0);
    expect(report.checks.length).toBeGreaterThan(0);
    expect(report.quality.files[0]?.codeLines).toBeGreaterThan(0);
    expect(report.review.filesOmitted).toEqual([]);
  });

  it("surfaces FastAPI validation errors as readable messages", async () => {
    server.use(
      http.post("*/api/review/snippet", () =>
        HttpResponse.json(
          { detail: [{ msg: "String should have at least 1 character" }] },
          { status: 422 },
        ),
      ),
    );

    const error = await captureError();

    expect(error.status).toBe(422);
    expect(error.message).toBe("String should have at least 1 character");
  });

  it("keeps the grader's reason for turning input down", async () => {
    server.use(
      http.post("*/api/review/snippet", () =>
        HttpResponse.json(fixtures.rejectedNotCode, { status: 422 }),
      ),
    );

    const error = await captureError();

    expect(error.status).toBe(422);
    expect(error.code).toBe("not_code");
  });

  it("rejects responses that break the contract", async () => {
    server.use(http.post("*/api/review/snippet", () => HttpResponse.json({ summary: "?" })));

    const error = await captureError();

    expect(error.message).toMatch(/unexpected response/);
  });

  it("reports an unreachable service as offline (status null)", async () => {
    server.use(http.post("*/api/review/snippet", () => HttpResponse.error()));

    expect((await captureError()).status).toBeNull();
  });

  it("does not turn a cancelled request into an API error", async () => {
    const controller = new AbortController();
    controller.abort();

    const outcome = await reviewSnippet(payload, controller.signal).catch(
      (error: unknown) => error,
    );

    expect(outcome).not.toBeInstanceOf(AnalyzerApiError);
    expect(outcome).toHaveProperty("name", "AbortError");
  });
});
