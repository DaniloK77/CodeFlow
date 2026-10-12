import { beforeEach, describe, expect, it } from "vitest";

import {
  type Attempt,
  compareAttempts,
  findPrevious,
  MAX_ATTEMPTS,
  readAttempts,
  taskKeyFor,
  toAttempt,
  writeAttempts,
} from "./history";
import { analysisReportSchema } from "./schema";
import quality from "@/test/fixtures/quality-todo-list.json";
import graded from "@/test/fixtures/review-todo-list.json";

const attempt = (overrides: Partial<Attempt> = {}): Attempt => ({
  id: "a",
  at: 1,
  name: "TodoList.jsx",
  taskKey: "TodoList.jsx::build a todo list",
  quality: 50,
  overall: null,
  grade: null,
  findings: [],
  ...overrides,
});

const finding = (rule: string) => ({ rule, severity: "warning" as const, message: rule });

describe("attempt history", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("round-trips through storage", () => {
    writeAttempts([attempt()]);

    expect(readAttempts()).toEqual([attempt()]);
  });

  it("ignores storage that is corrupt, from another version or unavailable", () => {
    window.localStorage.setItem("codeflow.attempts.v1", "{not json");
    expect(readAttempts()).toEqual([]);

    window.localStorage.setItem("codeflow.attempts.v1", JSON.stringify([{ id: 1 }]));
    expect(readAttempts()).toEqual([]);

    const blocked = {
      getItem: () => {
        throw new Error("blocked");
      },
      setItem: () => {
        throw new Error("full");
      },
    } as unknown as Storage;
    expect(readAttempts(blocked)).toEqual([]);
    expect(() => {
      writeAttempts([attempt()], blocked);
    }).not.toThrow();
  });

  it("keeps only the newest attempts", () => {
    const many = Array.from({ length: MAX_ATTEMPTS + 5 }, (_, index) =>
      attempt({ id: String(index) }),
    );
    writeAttempts(many);

    expect(readAttempts()).toHaveLength(MAX_ATTEMPTS);
  });

  it("summarises a report, with and without a rank", () => {
    const withoutAi = toAttempt(analysisReportSchema.parse(quality), "Build a todo list", 10);
    const withAi = toAttempt(analysisReportSchema.parse(graded), "Build a todo list", 11);

    expect(withoutAi).toMatchObject({ overall: null, grade: null, at: 10 });
    expect(withoutAi.quality).toBe(analysisReportSchema.parse(quality).quality.score);
    expect(withAi).toMatchObject({ grade: "Poor", overall: 64 });
    expect(withAi.findings.length).toBeGreaterThan(0);
  });

  it("matches attempts by task and file, ignoring case and spacing", () => {
    expect(taskKeyFor("Build  a TODO\nlist", "A.jsx")).toBe(
      taskKeyFor("build a todo list", "A.jsx"),
    );
    expect(taskKeyFor("Build a todo list", "A.jsx")).not.toBe(
      taskKeyFor("Build a todo list", "B.jsx"),
    );
  });

  it("finds the latest earlier attempt at the same task", () => {
    const current = attempt({ id: "c" });
    const attempts = [
      current,
      attempt({ id: "other", taskKey: "different" }),
      attempt({ id: "p1" }),
      attempt({ id: "p2" }),
    ];

    expect(findPrevious(attempts, current)?.id).toBe("p1");
    expect(findPrevious([current], current)).toBeUndefined();
  });

  it("compares scores and which rules were fixed or introduced", () => {
    const previous = attempt({
      quality: 46,
      overall: 40,
      findings: [finding("short-names"), finding("no-tests"), finding("magic-numbers")],
    });
    const current = attempt({
      id: "b",
      quality: 62,
      overall: 55,
      findings: [finding("no-tests"), finding("no-types"), finding("no-types")],
    });

    const comparison = compareAttempts(previous, current);

    expect(comparison.qualityDelta).toBe(16);
    expect(comparison.overallDelta).toBe(15);
    expect(comparison.resolved).toEqual([
      { rule: "magic-numbers", change: -1 },
      { rule: "short-names", change: -1 },
    ]);
    expect(comparison.added).toEqual([{ rule: "no-types", change: 2 }]);
  });

  it("has no overall change unless both attempts were fully graded", () => {
    const comparison = compareAttempts(
      attempt({ overall: null }),
      attempt({ id: "b", overall: 70 }),
    );

    expect(comparison.overallDelta).toBeNull();
  });
});
