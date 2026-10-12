/** Rules that describe a whole file; they are reported on line 1, which they don't point at. */
export const FILE_LEVEL_RULES: ReadonlySet<string> = new Set([
  "file-length",
  "deep-nesting",
  "no-tests",
]);

/** The line a finding points at, or null when it concerns the file as a whole. */
export function lineOf(finding: { rule: string; line: number }): number | null {
  return FILE_LEVEL_RULES.has(finding.rule) ? null : finding.line;
}

const SEVERITY_RANK = { error: 0, warning: 1, info: 2 } as const;

/** Errors first, then warnings, then notes; ties keep source order. */
export function bySeverity<T extends { severity: keyof typeof SEVERITY_RANK; line: number }>(
  findings: readonly T[],
): T[] {
  return [...findings].sort(
    (a, b) => SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity] || a.line - b.line,
  );
}
