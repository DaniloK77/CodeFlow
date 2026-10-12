import { describeRule } from "@/features/analyzer/ruleDocs";
import { bySeverity } from "@/lib/findings";
import type { ExampleReport } from "@/types/content";

const SHOWN_FINDINGS = 3;

const DOT = { error: "bg-rose-400", warning: "bg-amber-400", info: "bg-slate-400" } as const;

/**
 * Floating result card: what the real static analysis found in the example in the active tab.
 * There is deliberately no rank here, because a rank needs the AI to verify the task.
 */
export function HighlightCard({ report }: { report: ExampleReport }) {
  const top = bySeverity(report.findings).slice(0, SHOWN_FINDINGS);
  const more = report.findings.length - top.length;

  return (
    <div
      data-testid="highlight-card"
      className="absolute right-4 bottom-4 hidden w-80 translate-x-8 translate-y-8 rounded-xl border border-white/20 bg-slate-900/80 p-4 shadow-2xl backdrop-blur-xl lg:block"
    >
      <div className="mb-3 flex items-center justify-between">
        <span className="text-xs tracking-wide text-gray-300 uppercase">Code quality</span>
        <span className="text-sm text-gray-300 tabular-nums">
          <span className="text-2xl font-bold text-blue-300">{report.quality}</span>/100
        </span>
      </div>
      {top.length === 0 ? (
        <p className="text-left text-sm text-emerald-300">No findings. Nothing to fix.</p>
      ) : (
        <ul className="space-y-1.5 text-left text-xs text-gray-200">
          {top.map((finding) => (
            <li key={`${finding.rule}:${finding.line}`} className="flex gap-2">
              <span
                aria-hidden="true"
                className={`mt-1 size-2 shrink-0 rounded-full ${DOT[finding.severity]}`}
              />
              <span>
                <span className="font-semibold">{describeRule(finding.rule).title}</span>
                <span className="text-gray-400"> · line {finding.line}</span>
              </span>
            </li>
          ))}
          {more > 0 && <li className="pl-4 text-gray-400">+ {more} more in the full report</li>}
        </ul>
      )}
      <p className="mt-3 border-t border-white/10 pt-2 text-left text-xs text-gray-400">
        Real output of the static analysis. The rank needs the AI review of your task.
      </p>
    </div>
  );
}
