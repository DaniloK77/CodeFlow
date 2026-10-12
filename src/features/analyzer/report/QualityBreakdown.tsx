import { DIMENSION_LABELS, DIMENSIONS } from "../dimensions";
import type { AnalysisReport } from "../schema";

/** Where the code-quality points went, by dimension. The parts add up to 100 − code score. */
export function QualityBreakdown({ quality }: { quality: AnalysisReport["quality"] }) {
  const lost = 100 - quality.codeScore;
  return (
    <div className="space-y-3 rounded-xl border border-white/10 bg-white/5 p-4">
      <p className="text-sm text-gray-300">
        {lost === 0
          ? "No points lost: the static analyzer found nothing to fix."
          : `The code lost ${lost} points. Here is where they went:`}
      </p>
      <ul className="space-y-2">
        {DIMENSIONS.map((dimension) => {
          const points = quality.pointsLost[dimension];
          return (
            <li
              key={dimension}
              className="grid grid-cols-[8rem_1fr_3rem] items-center gap-3 text-sm"
            >
              <span className="text-gray-400">{DIMENSION_LABELS[dimension]}</span>
              <span className="h-2 overflow-hidden rounded-full bg-white/10">
                <span
                  className="block h-full rounded-full bg-rose-400/80"
                  style={{ width: `${Math.min(100, points)}%` }}
                />
              </span>
              <span className="text-right tabular-nums">{points > 0 ? `−${points}` : "0"}</span>
            </li>
          );
        })}
      </ul>
      {quality.hygieneScore !== null && (
        <p className="text-xs text-gray-500">
          Project score = 75% code ({quality.codeScore}) + 25% hygiene ({quality.hygieneScore}) ={" "}
          {quality.score}
        </p>
      )}
    </div>
  );
}
