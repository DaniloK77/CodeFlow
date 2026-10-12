import { ArrowDown, ArrowRight, ArrowUp, Minus } from "lucide-react";

import { cn } from "@/lib/cn";

import type { Comparison, RuleChange } from "../history";
import { describeRule } from "../ruleDocs";

/** Before and after: how this attempt differs from the previous one at the same task. */
export function AttemptComparison({
  comparison,
  currentQuality,
}: {
  comparison: Comparison;
  currentQuality: number;
}) {
  const { previous, qualityDelta, resolved, added } = comparison;
  const when = new Date(previous.at).toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });

  return (
    <section
      aria-labelledby="comparison-title"
      className="space-y-3 rounded-xl border border-white/10 bg-white/5 p-4"
    >
      <h3 id="comparison-title" className="text-sm font-semibold">
        Compared with your previous attempt{" "}
        <span className="font-normal text-gray-400">({when})</span>
      </h3>
      <p className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm">
        <span className="text-gray-400">Code quality</span>
        <span className="font-semibold tabular-nums">{previous.quality}</span>
        <ArrowRight aria-hidden="true" className="size-4 text-gray-500" />
        <span className="font-semibold tabular-nums">{currentQuality}</span>
        <Delta value={qualityDelta} />
        {comparison.overallDelta !== null && (
          <>
            <span className="ml-2 text-gray-400">Overall</span>
            <Delta value={comparison.overallDelta} />
          </>
        )}
      </p>
      <div className="grid gap-3 text-sm sm:grid-cols-2">
        <ChangeList title="Fixed" tone="good" changes={resolved} />
        <ChangeList title="New" tone="bad" changes={added} />
      </div>
    </section>
  );
}

function Delta({ value }: { value: number }) {
  const { Icon, label } = describeDelta(value);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums",
        value > 0 && "bg-emerald-500/15 text-emerald-300",
        value < 0 && "bg-rose-500/15 text-rose-300",
        value === 0 && "bg-white/10 text-gray-300",
      )}
    >
      <Icon aria-hidden="true" className="size-3" />
      {value > 0 ? `+${value}` : value}
      <span className="sr-only"> ({label})</span>
    </span>
  );
}

function ChangeList({
  title,
  tone,
  changes,
}: {
  title: string;
  tone: "good" | "bad";
  changes: readonly RuleChange[];
}) {
  return (
    <div>
      <p
        className={cn(
          "mb-1 text-xs font-semibold",
          tone === "good" ? "text-emerald-300" : "text-rose-300",
        )}
      >
        {title}
      </p>
      {changes.length === 0 ? (
        <p className="text-xs text-gray-500">Nothing</p>
      ) : (
        <ul className="space-y-1 text-xs text-gray-300">
          {changes.map(({ rule, change }) => (
            <li key={rule}>
              {describeRule(rule).title}
              {Math.abs(change) > 1 && <span className="text-gray-500"> ×{Math.abs(change)}</span>}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function describeDelta(value: number) {
  if (value > 0) return { Icon: ArrowUp, label: `up ${value}` };
  if (value < 0) return { Icon: ArrowDown, label: `down ${-value}` };
  return { Icon: Minus, label: "unchanged" };
}
