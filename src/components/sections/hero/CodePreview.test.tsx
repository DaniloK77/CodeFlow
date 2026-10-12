import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ASSIGNMENT_EXAMPLES } from "@/content/examples";
import { EXAMPLE_REPORTS } from "@/content/exampleReports";
import { nth } from "@/test/utils";

import { CodePreview } from "./CodePreview";

const fileNames = ASSIGNMENT_EXAMPLES.map((sample) => sample.fileName);

function renderPreview() {
  const user = userEvent.setup();
  render(<CodePreview samples={ASSIGNMENT_EXAMPLES} />);
  return { user, tabs: screen.getAllByRole("tab") };
}

describe("CodePreview", () => {
  it("renders one tab per sample with the first one selected", () => {
    const { tabs } = renderPreview();

    expect(tabs.map((tab) => tab.textContent)).toEqual(fileNames);
    expect(nth(tabs, 0)).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel")).toHaveAccessibleName(nth(fileNames, 0));
  });

  it("switches the code and the findings card when a tab is clicked", async () => {
    const { user } = renderPreview();
    const target = nth(ASSIGNMENT_EXAMPLES, 1);

    await user.click(screen.getByRole("tab", { name: target.fileName }));

    expect(screen.getByRole("tab", { name: target.fileName })).toHaveAttribute(
      "aria-selected",
      "true",
    );
    expect(screen.getByRole("tabpanel")).toHaveAccessibleName(target.fileName);
    expect(screen.getByTestId("highlight-card")).toHaveTextContent(
      `${EXAMPLE_REPORTS[target.id]?.quality}/100`,
    );
    expect(screen.getByTestId("highlight-card")).not.toHaveTextContent(/Excellent|Good|Poor/);
    expect(screen.getByText(target.task, { exact: false })).toBeInTheDocument();
  });

  it("supports arrow, Home and End keys with wrap-around", async () => {
    const { user, tabs } = renderPreview();
    const [first, second, last] = [nth(tabs, 0), nth(tabs, 1), nth(tabs, -1)];

    await user.click(first);
    await user.keyboard("{ArrowRight}");
    expect(second).toHaveFocus();
    expect(second).toHaveAttribute("aria-selected", "true");

    await user.keyboard("{End}");
    expect(last).toHaveFocus();

    await user.keyboard("{ArrowRight}");
    expect(first).toHaveFocus();

    await user.keyboard("{ArrowLeft}");
    expect(last).toHaveFocus();

    await user.keyboard("{Home}");
    expect(first).toHaveFocus();
  });

  it("keeps only the selected tab in the tab order", async () => {
    const { user, tabs } = renderPreview();

    await user.click(nth(tabs, 2));

    expect(tabs.map((tab) => tab.tabIndex)).toEqual([-1, -1, 0]);
  });

  it("renders nothing without samples", () => {
    const { container } = render(<CodePreview samples={[]} />);
    expect(container).toBeEmptyDOMElement();
  });
});
