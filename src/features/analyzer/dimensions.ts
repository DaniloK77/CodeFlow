// The six quality dimensions of codegrade (tools/codegrade/models.py). Kept free of runtime
// dependencies so the landing page can use them without downloading the analyzer's code.

export const DIMENSIONS = [
  "reliability",
  "complexity",
  "readability",
  "documentation",
  "accessibility",
  "testing",
] as const;
export type Dimension = (typeof DIMENSIONS)[number];

export const DIMENSION_LABELS: Record<Dimension, string> = {
  reliability: "Reliability",
  complexity: "Complexity",
  readability: "Readability",
  documentation: "Docs & types",
  accessibility: "Accessibility",
  testing: "Testing",
};

export const DIMENSION_SUMMARIES: Record<Dimension, string> = {
  reliability: "Bugs, security holes and missing error handling",
  complexity: "Structure that makes code hard to change",
  readability: "What the next reader has to decode",
  documentation: "Types and docs that explain how to use the code",
  accessibility: "Whether everyone can use the interface",
  testing: "Evidence that the code is verified",
};
