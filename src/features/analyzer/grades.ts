import type { Severity } from "./schema";

export const SEVERITY_STYLES: Record<Severity, { label: string; dot: string; line: string }> = {
  error: { label: "Errors", dot: "bg-rose-400", line: "bg-rose-500/15" },
  warning: { label: "Warnings", dot: "bg-amber-400", line: "bg-amber-500/10" },
  info: { label: "Notes", dot: "bg-slate-400", line: "bg-slate-500/10" },
};
