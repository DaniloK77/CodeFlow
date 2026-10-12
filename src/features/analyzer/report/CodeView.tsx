import { CodeBlock } from "@/components/ui/CodeBlock";
import { languageForPath } from "@/lib/languages";

import { SEVERITY_STYLES } from "../grades";
import type { Finding, Severity } from "../schema";
import { type ActiveLine, lineAnchorId, lineOf } from "./lines";

const CODE_STYLE = {
  maxHeight: "24rem",
  padding: "1rem 0",
  borderRadius: "0.75rem",
  fontSize: "12px",
  lineHeight: "1.6",
  background: "#011627",
} as const;

const SEVERITY_RANK: Record<Severity, number> = { error: 0, warning: 1, info: 2 };

interface CodeViewProps {
  code: string;
  path: string;
  findings: readonly Finding[];
  /** A line to bring into view and flash, e.g. after clicking a finding. */
  activeLine?: ActiveLine | null;
}

/** The analysed code, with every line that has a finding tinted by its worst severity. */
export function CodeView({ code, path, findings, activeLine }: CodeViewProps) {
  const worstByLine = new Map<number, Severity>();
  for (const finding of findings) {
    const line = lineOf(finding);
    if (line === null) continue;
    const current = worstByLine.get(line);
    if (current === undefined || SEVERITY_RANK[finding.severity] < SEVERITY_RANK[current]) {
      worstByLine.set(line, finding.severity);
    }
  }

  return (
    <div>
      <CodeBlock
        code={code}
        language={languageForPath(path)}
        style={CODE_STYLE}
        showLineNumbers
        getLineProps={(lineNumber) => {
          const severity = worstByLine.get(lineNumber);
          const flash = flashClass(activeLine, lineNumber);
          return {
            id: lineAnchorId(lineNumber),
            className: `block px-4 ${severity ? SEVERITY_STYLES[severity].line : ""} ${flash}`,
          };
        }}
      />
      <p role="status" className="sr-only">
        {activeLine ? `Showing line ${activeLine.line} in the code` : ""}
      </p>
    </div>
  );
}

/** Alternating two identical animations restarts the flash on repeated clicks. */
function flashClass(activeLine: ActiveLine | null | undefined, line: number): string {
  if (activeLine?.line !== line) return "";
  return activeLine.nonce % 2 === 0
    ? "motion-safe:animate-line-flash-a"
    : "motion-safe:animate-line-flash-b";
}
