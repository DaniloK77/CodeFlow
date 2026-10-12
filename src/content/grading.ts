import type { GradeName } from "@/types/content";

/** Share of the final grade, in percent. Must match the API (checked by content.test.ts). */
export const GRADE_WEIGHTS = { task: 50, quality: 35, explanation: 15 } as const;

export const GRADE_BANDS: readonly { grade: GradeName; min: number; max: number }[] = [
  { grade: "Excellent", min: 90, max: 100 },
  { grade: "Good", min: 70, max: 89 },
  { grade: "Poor", min: 0, max: 69 },
];

export interface GradingPart {
  id: keyof typeof GRADE_WEIGHTS;
  title: string;
  question: string;
  how: string;
  gradedBy: string;
}

export const GRADING_PARTS: readonly GradingPart[] = [
  {
    id: "task",
    title: "Solves the task",
    question: "Does the code do what the assignment asks?",
    how: "The task is split into requirements. Met ones count fully, partly met ones count half, and each bug costs points.",
    gradedBy: "AI review",
  },
  {
    id: "quality",
    title: "Code quality",
    question: "Is it reliable, readable and maintainable?",
    how: "Starts at 100 and every finding costs points: 15 for an error, 7 for a warning, 3 for a note. Missing tests, types and docs count as findings. Code that doesn't parse can't score above 40.",
    gradedBy: "Static analysis",
  },
  {
    id: "explanation",
    title: "Explanation",
    question: "Can you explain how your solution works?",
    how: "Accuracy against the code (50 points), completeness (30) and clarity (20).",
    gradedBy: "AI review",
  },
];
