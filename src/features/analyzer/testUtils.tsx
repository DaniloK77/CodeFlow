import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { App } from "@/App";
import { ASSIGNMENT_EXAMPLES } from "@/content/examples";
import { GRADE_PATH } from "@/lib/routes";

export type User = ReturnType<typeof userEvent.setup>;

/** Opens the grading screen the way a visitor does: by loading its URL. */
export async function renderGradePage(user: User = userEvent.setup()): Promise<User> {
  window.history.replaceState(null, "", GRADE_PATH);
  render(<App />);
  // The page is lazy-loaded; the first import is transformed on demand, so allow extra time.
  await screen.findByRole("heading", { level: 1, name: "Grade your solution" }, { timeout: 5_000 });
  return user;
}

export function submit(user: User, name = "Grade my solution"): Promise<void> {
  return user.click(screen.getByRole("button", { name }));
}

/** Loads one of the built-in examples (task, code and explanation) and submits it. */
export async function gradeExample(user: User, id: string): Promise<void> {
  const example = ASSIGNMENT_EXAMPLES.find((candidate) => candidate.id === id);
  if (!example) throw new Error(`unknown example ${id}`);
  await user.click(screen.getByRole("button", { name: example.label }));
  await submit(user);
}

/** Fills the two text steps with valid answers. */
export async function describeAssignment(user: User): Promise<void> {
  await user.type(screen.getByLabelText(/the task/i), "Write a function that adds two numbers.");
  await user.type(
    screen.getByLabelText(/your explanation/i),
    "It returns the sum of both arguments using the plus operator.",
  );
}
