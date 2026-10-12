import { screen, within } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { ASSIGNMENT_EXAMPLES } from "@/content/examples";
import { fixtures, server } from "@/test/server";
import { nth } from "@/test/utils";

import { describeAssignment, gradeExample, renderGradePage, submit } from "./testUtils";

describe("grading screen", () => {
  it("shows the form and, beside it, what the report will contain", async () => {
    await renderGradePage();

    expect(screen.getByLabelText(/the task/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/your explanation/i)).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Your report will appear here" })).toBeVisible();
    expect(await screen.findByText(/AI review off: code quality only/)).toBeInTheDocument();
  });

  it("fills the task, the code and the explanation from an example", async () => {
    const user = await renderGradePage();
    const example = nth(ASSIGNMENT_EXAMPLES, 1);

    await user.click(screen.getByRole("button", { name: example.label }));

    expect(screen.getByLabelText(/the task/i)).toHaveValue(example.task);
    expect(screen.getByLabelText(/your explanation/i)).toHaveValue(example.explanation);
    expect(screen.getByLabelText("Your code")).toHaveValue(example.code);
  });

  it("ranks a submission once the AI review has verified the task", async () => {
    const user = await renderGradePage();

    await gradeExample(user, "todo-list");

    expect(
      await screen.findByRole("img", { name: /Overall score 64 out of 100: Poor/ }),
    ).toBeVisible();
    expect(screen.getByText("Does it solve the task? 59/100")).toBeInTheDocument();
    expect(screen.getByText("Show how many tasks are still left")).toHaveTextContent("(missing)");
    expect(screen.getByText("Empty tasks can be added")).toBeInTheDocument();
    expect(screen.getByText("Your explanation 85/100")).toBeInTheDocument();
    expect(screen.getByText("Render the number of tasks that aren't done")).toBeInTheDocument();
    expect(screen.getByText("Code quality 62/100")).toBeInTheDocument();
    expect(screen.getByText("Click on a non-interactive element")).toBeInTheDocument();
  });

  it("gives code quality alone a score but no rank, and says the task is unverified", async () => {
    const user = await renderGradePage();

    await gradeExample(user, "pair-sums");

    expect(await screen.findByRole("img", { name: "Code quality 46 out of 100" })).toBeVisible();
    expect(screen.getByText("Task not verified")).toBeInTheDocument();
    expect(screen.getByText("Task and explanation weren't graded")).toBeInTheDocument();
    expect(screen.getAllByText("not verified")).toHaveLength(2);
    expect(screen.queryByText(/^(Excellent|Good|Poor)$/)).not.toBeInTheDocument();
  });

  it("shows what could be verified without AI: names from the task, looked up in the code", async () => {
    const user = await renderGradePage();

    await gradeExample(user, "pair-sums");

    const heading = await screen.findByText("What we could verify without AI");
    const section = heading.parentElement;
    if (!section) throw new Error("the checks have no section");
    const checks = within(section);
    expect(checks.getByText("find_pairs")).toBeInTheDocument();
    expect(checks.getAllByText(/not defined|the task names it/)[0]).toBeInTheDocument();
  });

  it("lists what is missing instead of sending an incomplete submission", async () => {
    const onRequest = vi.fn();
    server.use(http.post("*/api/review/snippet", onRequest));
    const user = await renderGradePage();

    await submit(user);

    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Describe the task");
    expect(alert).toHaveTextContent("Paste your code");
    expect(alert).toHaveTextContent("Explain your solution");
    expect(onRequest).not.toHaveBeenCalled();
  });

  it("grades a zipped project with a file table and hygiene checklist", async () => {
    const user = await renderGradePage();
    await describeAssignment(user);
    await user.click(screen.getByRole("tab", { name: /zip project/i }));

    await user.upload(
      screen.getByLabelText(/drop your project/i),
      new File(["PK"], "homework.zip", { type: "application/zip" }),
    );
    await submit(user);

    const table = await screen.findByRole("table");
    expect(nth(within(table).getAllByRole("row"), 1)).toHaveTextContent("src/pair_sums.py");
    expect(within(table).queryByRole("columnheader", { name: "Grade" })).not.toBeInTheDocument();
    expect(screen.getByText("README")).toBeInTheDocument();
  });

  it("explains when the grading service is offline", async () => {
    server.use(http.post("*/api/review/snippet", () => HttpResponse.error()));
    const user = await renderGradePage();

    await gradeExample(user, "user-list");

    expect(await screen.findByRole("alert")).toHaveTextContent(/offline.*npm run dev/s);
  });

  it("explains why the grader turned the input down", async () => {
    server.use(
      http.post("*/api/review/snippet", () =>
        HttpResponse.json(fixtures.rejectedNotCode, { status: 422 }),
      ),
    );
    const user = await renderGradePage();

    await gradeExample(user, "user-list");

    const alert = await screen.findByRole("alert");
    expect(alert).toHaveTextContent("That doesn't look like code");
    expect(alert).toHaveTextContent("Paste the function, component or script you wrote");
  });

  it("tells the visitor when to retry after a burst of requests", async () => {
    server.use(
      http.post("*/api/review/snippet", () =>
        HttpResponse.json(
          { detail: "Too many requests." },
          { status: 429, headers: { "Retry-After": "12" } },
        ),
      ),
    );
    const user = await renderGradePage();

    await gradeExample(user, "user-list");

    expect(await screen.findByRole("alert")).toHaveTextContent("try again in 12 s");
  });

  it("shows honest progress while grading and lets the visitor cancel", async () => {
    server.use(http.post("*/api/review/snippet", () => new Promise<never>(() => undefined)));
    const user = await renderGradePage();

    await gradeExample(user, "user-list");

    const progress = await screen.findByRole("status", { name: "Grading progress" });
    expect(progress).toHaveTextContent("Grading your solution…");
    expect(progress).toHaveTextContent("can take up to a minute");

    await user.click(screen.getByRole("button", { name: "Cancel" }));
    expect(screen.getByRole("heading", { name: "Your report will appear here" })).toBeVisible();
  });

  it("scrolls to the flagged line when a finding is chosen", async () => {
    const scrollIntoView = vi.fn();
    Element.prototype.scrollIntoView = scrollIntoView;
    const user = await renderGradePage();
    await gradeExample(user, "todo-list");

    const [finding] = await screen.findAllByRole("button", { name: /^Show line \d+ in the code/ });
    if (!finding) throw new Error("no finding offers to show its line");
    await user.click(finding);

    const line = /Show line (\d+)/.exec(finding.getAttribute("aria-label") ?? "")?.[1];
    expect(scrollIntoView).toHaveBeenCalledWith({ block: "center", behavior: "smooth" });
    expect(document.getElementById(`code-line-${line}`)).toBeInTheDocument();
    expect(screen.getByText(`Showing line ${line} in the code`)).toBeInTheDocument();
  });

  it("downloads the report, and starts a new submission from scratch", async () => {
    const click = vi
      .spyOn(HTMLAnchorElement.prototype, "click")
      .mockImplementation(() => undefined);
    URL.createObjectURL = vi.fn(() => "blob:report");
    URL.revokeObjectURL = vi.fn();
    const user = await renderGradePage();
    await gradeExample(user, "user-list");

    await user.click(await screen.findByRole("button", { name: "Download JSON report" }));
    expect(click).toHaveBeenCalledOnce();

    await user.click(screen.getByRole("button", { name: "Start a new submission" }));
    expect(screen.getByLabelText(/the task/i)).toHaveValue("");
    expect(screen.getByRole("heading", { name: "Your report will appear here" })).toBeVisible();
  });
});

describe("attempt history", () => {
  const improved = () => {
    const original = fixtures.pairSumsQuality;
    const [file] = original.quality.files;
    if (!file) throw new Error("fixture has no file");
    return {
      ...original,
      scores: { ...original.scores, quality: 70 },
      quality: {
        ...original.quality,
        score: 70,
        files: [{ ...file, score: 70, findings: file.findings.slice(0, 2) }],
      },
    };
  };

  it("keeps the form after grading, so a fix can be graded again and compared", async () => {
    const user = await renderGradePage();
    await gradeExample(user, "pair-sums");
    await screen.findByRole("img", { name: "Code quality 46 out of 100" });
    expect(screen.queryByText(/Compared with your previous attempt/)).not.toBeInTheDocument();

    server.use(http.post("*/api/review/snippet", () => HttpResponse.json(improved())));
    await user.type(screen.getByLabelText("Your code"), "\n# fixed");
    await submit(user, "Grade again");

    expect(await screen.findByRole("img", { name: "Code quality 70 out of 100" })).toBeVisible();
    const comparison = screen.getByRole("region", { name: /Compared with your previous attempt/ });
    expect(comparison).toHaveTextContent("46");
    expect(comparison).toHaveTextContent("+24");
    expect(within(comparison).getByText("Fixed")).toBeInTheDocument();
  });

  it("lists every attempt, remembers them across visits and can clear them", async () => {
    const user = await renderGradePage();
    await gradeExample(user, "pair-sums");
    await screen.findByRole("img", { name: "Code quality 46 out of 100" });
    expect(screen.getByText("Your attempts (1)")).toBeInTheDocument();

    // A new visit: nothing is on screen, but the history is still there.
    document.body.replaceChildren();
    await renderGradePage(user);
    expect(screen.getByText("Your attempts (1)")).toBeInTheDocument();

    await user.click(screen.getByText("Your attempts (1)"));
    await user.click(screen.getByRole("button", { name: "Clear history" }));
    expect(screen.queryByText(/Your attempts/)).not.toBeInTheDocument();
  });
});
