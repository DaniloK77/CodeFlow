import type { AnalysisReport } from "../schema";

/** Saves the report as pretty-printed JSON, e.g. to attach to a pull request. */
export function downloadReport(report: AnalysisReport): void {
  const blob = new Blob([JSON.stringify(report, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `codegrade-${report.name.replace(/[^\w.-]+/g, "-")}.json`;
  link.click();
  URL.revokeObjectURL(url);
}
