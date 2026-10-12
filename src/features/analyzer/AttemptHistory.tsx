import { History, Trash2 } from "lucide-react";

import type { Attempt } from "./history";

/** Every grade in this browser, newest first. Stored locally; never uploaded. */
export function AttemptHistory({
  attempts,
  onClear,
}: {
  attempts: readonly Attempt[];
  onClear: () => void;
}) {
  if (attempts.length === 0) return null;
  return (
    <details className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm">
      <summary className="flex cursor-pointer items-center gap-2 font-medium">
        <History aria-hidden="true" className="size-4 text-gray-400" />
        Your attempts ({attempts.length})
      </summary>
      <ol className="mt-3 divide-y divide-white/5">
        {attempts.map((attempt) => (
          <li key={attempt.id} className="flex flex-wrap items-baseline justify-between gap-2 py-2">
            <span className="min-w-0">
              <span className="font-mono text-xs break-all">{attempt.name}</span>{" "}
              <time className="text-xs text-gray-500" dateTime={new Date(attempt.at).toISOString()}>
                {new Date(attempt.at).toLocaleString("en-US", {
                  month: "short",
                  day: "numeric",
                  hour: "numeric",
                  minute: "2-digit",
                })}
              </time>
            </span>
            <span className="text-xs text-gray-300 tabular-nums">
              quality {attempt.quality}
              {attempt.grade !== null && attempt.overall !== null
                ? ` · ${attempt.grade} ${attempt.overall}`
                : " · task not verified"}
            </span>
          </li>
        ))}
      </ol>
      <div className="mt-3 flex flex-wrap items-center justify-between gap-2 border-t border-white/10 pt-3">
        <p className="text-xs text-gray-500">Saved in this browser only.</p>
        <button
          type="button"
          onClick={onClear}
          className="flex items-center gap-1.5 rounded-lg border border-white/10 px-3 py-1.5 text-xs text-gray-300 transition-colors hover:bg-white/10"
        >
          <Trash2 aria-hidden="true" className="size-3.5" />
          Clear history
        </button>
      </div>
    </details>
  );
}
