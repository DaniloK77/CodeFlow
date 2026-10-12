import type { AssignmentReview } from "../schema";

type Assessment = NonNullable<AssignmentReview["explanation"]>;

const RATINGS: Record<string, { label: string; tone: "good" | "fair" | "poor" }> = {
  accurate: { label: "Accurate", tone: "good" },
  partially_accurate: { label: "Partly accurate", tone: "fair" },
  inaccurate: { label: "Inaccurate", tone: "poor" },
  complete: { label: "Complete", tone: "good" },
  partial: { label: "Incomplete", tone: "fair" },
  minimal: { label: "Minimal", tone: "poor" },
  clear: { label: "Clear", tone: "good" },
  understandable: { label: "Understandable", tone: "fair" },
  unclear: { label: "Unclear", tone: "poor" },
};

const TONES = {
  good: "border-emerald-400/30 bg-emerald-500/10 text-emerald-200",
  fair: "border-amber-400/30 bg-amber-500/10 text-amber-200",
  poor: "border-rose-400/30 bg-rose-500/10 text-rose-200",
} as const;

/** How well the explanation matches and describes the code. */
export function ExplanationReview({ assessment }: { assessment: Assessment }) {
  const aspects = [
    ["Accuracy", assessment.accuracy],
    ["Completeness", assessment.completeness],
    ["Clarity", assessment.clarity],
  ] as const;

  return (
    <div className="space-y-3 rounded-xl border border-white/10 bg-white/5 p-4">
      <dl className="flex flex-wrap gap-2">
        {aspects.map(([aspect, value]) => {
          const rating = RATINGS[value] ?? { label: value, tone: "fair" as const };
          return (
            <div
              key={aspect}
              className={`rounded-full border px-3 py-1 text-xs ${TONES[rating.tone]}`}
            >
              <dt className="inline">{aspect}: </dt>
              <dd className="inline font-semibold">{rating.label}</dd>
            </div>
          );
        })}
      </dl>
      <p className="text-sm text-gray-300">{assessment.feedback}</p>
    </div>
  );
}
