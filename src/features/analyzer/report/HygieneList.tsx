import { CircleCheck, CircleX } from "lucide-react";

import type { AnalysisReport } from "../schema";

export function HygieneList({ checks }: { checks: AnalysisReport["quality"]["hygiene"] }) {
  return (
    <ul className="grid gap-2 sm:grid-cols-2">
      {checks.map((check) => (
        <li
          key={check.name}
          className="flex gap-3 rounded-lg border border-white/10 bg-white/5 p-3 text-sm"
        >
          {check.passed ? (
            <CircleCheck aria-hidden="true" className="size-5 shrink-0 text-emerald-400" />
          ) : (
            <CircleX aria-hidden="true" className="size-5 shrink-0 text-rose-400" />
          )}
          <div>
            <p className="font-medium">
              {check.name}
              <span className="sr-only">{check.passed ? " (passed)" : " (missing)"}</span>
              <span className="ml-2 text-xs text-gray-500">{check.weight} pts</span>
            </p>
            {!check.passed && <p className="text-xs text-gray-400">{check.hint}</p>}
          </div>
        </li>
      ))}
    </ul>
  );
}
