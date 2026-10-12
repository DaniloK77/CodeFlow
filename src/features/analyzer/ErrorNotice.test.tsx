import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AnalyzerApiError } from "./api";
import { ErrorNotice } from "./ErrorNotice";

const notice = (error: AnalyzerApiError) => {
  render(<ErrorNotice error={error} />);
  return screen.getByRole("alert");
};

describe("ErrorNotice", () => {
  it.each([
    ["not_code", "That doesn't look like code"],
    ["unsupported_language", "That language isn't supported yet"],
    ["too_little_code", "There isn't enough code to grade"],
    ["analysis_timeout", "That took too long to analyse"],
  ])("explains the grader's refusal %s", (code, title) => {
    const alert = notice(new AnalyzerApiError("Reason from the grader.", 422, null, code));

    expect(alert).toHaveTextContent(title);
    expect(alert).toHaveTextContent("Reason from the grader.");
  });

  it("names the supported languages when one isn't", () => {
    const alert = notice(
      new AnalyzerApiError("This looks like Java.", 422, null, "unsupported_language"),
    );

    expect(alert).toHaveTextContent("JavaScript, TypeScript (including React) and Python");
  });

  it.each([
    [503, "The grader is busy"],
    [413, "That's too big for the free plan"],
    [500, "We couldn't grade that"],
  ])("explains HTTP %i", (status, title) => {
    expect(notice(new AnalyzerApiError("Server said no.", status))).toHaveTextContent(title);
  });

  it("falls back to a generic message for refusals it doesn't know yet", () => {
    const alert = notice(new AnalyzerApiError("Brand new reason.", 422, null, "something_new"));

    expect(alert).toHaveTextContent("We couldn't grade that");
    expect(alert).toHaveTextContent("Brand new reason.");
  });
});
