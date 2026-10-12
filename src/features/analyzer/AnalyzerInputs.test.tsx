import { fireEvent, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import { fixtures, server } from "@/test/server";

import { LIMITS } from "./constants";
import { describeAssignment, renderGradePage, submit } from "./testUtils";

describe("solution inputs", () => {
  it("sends a single file with its name, the task and the explanation", async () => {
    const received = vi.fn();
    server.use(
      http.post("*/api/review/snippet", async ({ request }) => {
        received(await request.json());
        return HttpResponse.json(fixtures.userListQuality);
      }),
    );
    const user = await renderGradePage();
    await describeAssignment(user);
    await user.click(screen.getByRole("tab", { name: /single file/i }));

    const file = new File(["export const add = (a: number, b: number) => a + b;\n"], "add.ts");
    await user.upload(screen.getByLabelText(/drop a component/i), file);
    await submit(user);

    expect(await screen.findByRole("img", { name: /Code quality 100 out of 100/ })).toBeVisible();
    expect(received).toHaveBeenCalledWith({
      task: "Write a function that adds two numbers.",
      explanation: "It returns the sum of both arguments using the plus operator.",
      code: "export const add = (a: number, b: number) => a + b;\n",
      language: "auto",
      filename: "add.ts",
    });
  });

  it("accepts a project dropped onto the drop zone", async () => {
    const user = await renderGradePage();
    await user.click(screen.getByRole("tab", { name: /zip project/i }));
    const zone = screen.getByText("Drop your project .zip here").closest("[role=presentation]");
    if (!zone) throw new Error("drop zone not found");

    fireEvent.dragOver(zone);
    fireEvent.drop(zone, { dataTransfer: { files: [new File(["PK"], "dropped.zip")] } });

    expect(screen.getByText("dropped.zip")).toBeInTheDocument();
  });

  it("rejects files the free plan can't take, with a reason", async () => {
    const user = await renderGradePage(userEvent.setup({ applyAccept: false }));
    await user.click(screen.getByRole("tab", { name: /single file/i }));

    await user.upload(screen.getByLabelText(/drop a component/i), new File(["x"], "notes.txt"));

    expect(screen.getByRole("alert")).toHaveTextContent("isn't supported");
  });

  it("lets the author pick a language and flags code over the size limit", async () => {
    const user = await renderGradePage();

    await user.selectOptions(screen.getByLabelText("Language"), "python");
    expect(screen.getByLabelText("Language")).toHaveValue("python");

    fireEvent.change(screen.getByLabelText("Your code"), {
      target: { value: "x".repeat(LIMITS.snippetChars + 1) },
    });
    await submit(user);
    expect(screen.getByRole("alert")).toHaveTextContent("over 200,000 characters");
  });

  it("counts down to the minimum length of the written answers", async () => {
    const user = await renderGradePage();

    await user.type(screen.getByLabelText(/the task/i), "Add numbers");

    expect(
      screen.getByText(`${LIMITS.taskMinChars - 11} more characters needed`),
    ).toBeInTheDocument();
  });
});
