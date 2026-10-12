import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PLANNED_PLANS_HREF, PRICING_PLANS } from "@/content/pricing";
import { formatPrice } from "@/lib/format";

import { Pricing } from "./Pricing";

describe("Pricing", () => {
  it.each(PRICING_PLANS)("renders the $name plan with its price and features", (plan) => {
    render(<Pricing />);

    const card = screen.getByRole("article", { name: plan.name });
    expect(within(card).getByText(formatPrice(plan.monthlyPrice))).toBeInTheDocument();
    expect(within(card).getAllByRole("listitem")).toHaveLength(plan.features.length);
  });

  it("offers a free plan and two paid plans in euros", () => {
    expect(PRICING_PLANS.map((plan) => formatPrice(plan.monthlyPrice))).toEqual([
      "€0",
      "€20",
      "€100",
    ]);
  });

  it("is honest about what exists: only the free plan is available", () => {
    render(<Pricing />);

    expect(
      within(screen.getByRole("article", { name: "Free" })).getByText("Available now"),
    ).toBeVisible();
    for (const name of ["Pro", "Classroom"]) {
      const card = screen.getByRole("article", { name });
      expect(within(card).getByText("Planned · not available yet")).toBeVisible();
    }
    expect(screen.queryByText(/Most Popular/)).not.toBeInTheDocument();
  });

  it("sends the free plan to the grading screen and collects interest for the others", () => {
    render(<Pricing />);

    expect(screen.getByRole("link", { name: "Grade my solution (Free plan)" })).toHaveAttribute(
      "href",
      "/grade",
    );
    for (const name of ["Pro", "Classroom"]) {
      expect(
        screen.getByRole("link", { name: `Tell us you're interested (${name} plan)` }),
      ).toHaveAttribute("href", PLANNED_PLANS_HREF);
    }
    expect(PLANNED_PLANS_HREF).toMatch(/^https:\/\/github\.com\//);
  });
});
