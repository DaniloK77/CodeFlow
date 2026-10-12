import { describe, expect, it } from "vitest";

import { fixtures } from "@/test/server";

import { EXAMPLE_REPORTS } from "./exampleReports";
import { ASSIGNMENT_EXAMPLES } from "./examples";
import { FEATURES } from "./features";
import { GRADE_BANDS, GRADE_WEIGHTS } from "./grading";
import { PRICING_PLANS } from "./pricing";

const ids = (items: readonly { id: string }[]) => items.map((item) => item.id);

describe("content", () => {
  it.each([
    ["features", ids(FEATURES)],
    ["pricing plans", ids(PRICING_PLANS)],
    ["examples", ids(ASSIGNMENT_EXAMPLES)],
    ["example file names", ASSIGNMENT_EXAMPLES.map((example) => example.fileName)],
  ])("%s have unique keys", (_name, keys) => {
    expect(new Set(keys).size).toBe(keys.length);
  });

  it("lists plans in ascending price order, and only the free one is available", () => {
    const prices = PRICING_PLANS.map((plan) => plan.monthlyPrice);
    expect(prices).toEqual([...prices].sort((a, b) => a - b));
    expect(PRICING_PLANS.filter((plan) => plan.status === "available").map((p) => p.id)).toEqual([
      "free",
    ]);
  });

  // The fixtures are real API output, so the hero can never advertise a result the engine
  // doesn't give. `npm run fixtures` re-records both when an example or a rule changes.
  it.each([
    ["pair-sums", fixtures.pairSumsQuality],
    ["todo-list", fixtures.todoListQuality],
    ["user-list", fixtures.userListQuality],
  ])("the hero's report for %s is what the engine gives", (id, report) => {
    const example = ASSIGNMENT_EXAMPLES.find((candidate) => candidate.id === id);
    const shown = EXAMPLE_REPORTS[id];
    const [file] = report.quality.files;

    expect(report.name).toBe(example?.fileName);
    expect(shown?.quality).toBe(report.quality.score);
    expect(shown?.findings).toEqual(
      file?.findings.map(({ rule, severity, line, message }) => ({
        rule,
        severity,
        line,
        message,
      })),
    );
  });

  it("shows examples from weak to strong, and a strong one that is earned", () => {
    const [weak, middling, strong] = ["pair-sums", "todo-list", "user-list"].map(
      (id) => EXAMPLE_REPORTS[id]?.quality ?? -1,
    );

    expect(weak).toBeLessThan(60);
    expect(weak).toBeLessThan(middling ?? 0);
    expect(middling).toBeLessThan(strong ?? 0);
    expect(strong).toBeGreaterThanOrEqual(90);
  });

  it("uses the same weights and grade bands as the API", () => {
    const { todoListReview } = fixtures;
    expect(todoListReview.weights).toEqual(GRADE_WEIGHTS);
    const band = GRADE_BANDS.find((candidate) => todoListReview.overall_score >= candidate.min);
    expect(band?.grade).toBe(todoListReview.grade);
  });

  it("recorded fixtures give a rank only to a completed review", () => {
    expect(fixtures.todoListReview).toMatchObject({ verdict: "graded", grade: "Poor" });
    for (const report of [fixtures.pairSumsQuality, fixtures.todoListQuality]) {
      expect(report).toMatchObject({ verdict: "quality_only", grade: null, overall_score: null });
    }
  });
});
