import type { Feature } from "@/types/content";

export const FEATURES: readonly Feature[] = [
  {
    id: "task-check",
    title: "Does It Solve the Task?",
    description:
      "The assignment is split into concrete requirements, and each one is checked against what your code actually does: met, partly met or missing, with the line that proves it. Bugs are listed separately.",
    tryItLabel: "Grade my solution for free",
    snippet: {
      language: "bash",
      code: `✔ Type a task and add it with a button   TodoList.jsx:7
✔ Mark a task as done by clicking it     TodoList.jsx:12
◐ Done tasks are crossed out             only a class is set
✖ Show how many tasks are still left     no count rendered

  Solves the task   59/100`,
    },
  },
  {
    id: "code-quality",
    title: "Code Quality, Measured",
    description:
      "A strict static analyzer scores reliability, complexity, readability, documentation, accessibility and testing, and shows where every point went. The same code always gets the same score.",
    snippet: {
      language: "bash",
      code: `✖ pair_sums.py:1   5 nested control blocks (limit 3)
▲ pair_sums.py:1   mutable default argument is shared across calls
▲ pair_sums.py:1   single-letter names (f, l, r)
▲ pair_sums.py:1   no tests

  Code quality   46/100   (task not verified)
  −18 complexity  −13 readability  −10 reliability  −7 testing`,
    },
  },
  {
    id: "explanation-review",
    title: "Explain Your Thinking",
    description:
      "Explaining your code is half of every technical interview. Your explanation is compared with the code for accuracy, then rated for completeness and clarity.",
    snippet: {
      language: "bash",
      code: `Accuracy       accurate
Completeness   partial   (doesn't mention the missing count)
Clarity        clear

  Explanation   85/100`,
    },
  },
  {
    id: "ci-quality-gate",
    title: "The Same Grade in Your Terminal",
    description:
      "Mentors and teams can run the same engine from the command line or in CI, and fail a build when a submission drops below the bar. Add the task and an explanation to get the full ranked grade.",
    snippet: {
      language: "bash",
      code: `$ python -m tools.codegrade src --fail-under 90

  CODE QUALITY   93/100
  Task not verified: no rank without an AI review of the task

  Add --task-file and --explanation-file for the full grade.`,
    },
  },
];
