import { CircleCheck, CircleDashed, CircleX } from "lucide-react";

import type { StaticCheck } from "../schema";

const STATUS = {
  found: { icon: CircleCheck, colour: "text-emerald-400", label: "found" },
  mismatch: { icon: CircleDashed, colour: "text-amber-400", label: "differs" },
  missing: { icon: CircleX, colour: "text-rose-400", label: "not in the code" },
} as const;

const SOURCE_LABELS = { task: "In the task", explanation: "In your explanation" } as const;

/**
 * Names the task and the explanation mention, looked up in the code without any AI. This is the
 * part of "does it solve the task" that can be checked for certain, so it is shown even when
 * the AI review isn't available.
 */
export function StaticChecks({ checks }: { checks: readonly StaticCheck[] }) {
  if (checks.length === 0) return null;
  return (
    <ul className="space-y-2">
      {checks.map((check) => {
        const status = STATUS[check.status];
        const Icon = status.icon;
        return (
          <li
            key={`${check.source}:${check.name}`}
            className="flex gap-3 rounded-lg border border-white/10 bg-white/5 p-3 text-sm"
          >
            <Icon aria-hidden="true" className={`mt-0.5 size-5 shrink-0 ${status.colour}`} />
            <div className="min-w-0">
              <p className="font-medium">
                <span className="text-xs font-normal text-gray-400">
                  {SOURCE_LABELS[check.source]}:{" "}
                </span>
                <code className="rounded bg-white/10 px-1.5 py-0.5 font-mono text-xs break-all">
                  {check.name}
                </code>
                <span className="sr-only"> ({status.label})</span>
              </p>
              <p className="text-xs text-gray-400">{check.detail}</p>
            </div>
          </li>
        );
      })}
    </ul>
  );
}
