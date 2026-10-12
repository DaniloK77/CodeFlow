import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DIMENSION_LABELS, DIMENSIONS } from "@/features/analyzer/dimensions";
import { rulesByDimension } from "@/features/analyzer/ruleDocs";

import { Rules } from "./Rules";

describe("Rules", () => {
  it("counts the rules it lists and groups them by dimension", () => {
    render(<Rules />);
    const grouped = rulesByDimension();
    const total = DIMENSIONS.reduce((sum, dimension) => sum + grouped[dimension].length, 0);

    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent(`${total} Checks Across`);
    for (const dimension of DIMENSIONS) {
      expect(
        screen.getByRole("heading", { name: new RegExp(DIMENSION_LABELS[dimension]) }),
      ).toBeVisible();
    }
  });

  it("explains every rule of a dimension on demand", () => {
    render(<Rules />);

    expect(screen.getByText("All 34 rules")).toBeInTheDocument();
    expect(screen.getAllByText(/hardcoded secret/i).length).toBeGreaterThan(0);
  });
});
