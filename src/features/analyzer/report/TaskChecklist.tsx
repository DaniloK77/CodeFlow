import { CircleCheck, CircleDashed, CircleX, Bug } from "lucide-react";

import type { AssignmentReview } from "../schema";

const STATUS = {
  met: { icon: CircleCheck, colour: "text-emerald-400", label: "met" },
  partial: { icon: CircleDashed, colour: "text-amber-400", label: "partly met" },
  missing: { icon: CircleX, colour: "text-rose-400", label: "missing" },
} as const;

/** The task split into requirements, each with a verdict and where in the code it shows. */
export function TaskChecklist({ review }: { review: AssignmentReview }) {
  return (
    <div className="space-y-3">
      <ul className="space-y-2">
        {review.requirements.map((item) => {
          const status = STATUS[item.status];
          const Icon = status.icon;
          return (
            <li
              key={item.requirement}
              className="flex gap-3 rounded-lg border border-white/10 bg-white/5 p-3 text-sm"
            >
              <Icon aria-hidden="true" className={`mt-0.5 size-5 shrink-0 ${status.colour}`} />
              <div>
                <p className="font-medium">
                  {item.requirement}
                  <span className="sr-only"> ({status.label})</span>
                </p>
                <p className="text-xs text-gray-400">{item.evidence}</p>
              </div>
            </li>
          );
        })}
      </ul>
      {review.bugs.length > 0 && (
        <ul aria-label="Bugs" className="space-y-2">
          {review.bugs.map((bug) => (
            <li
              key={`${bug.location}:${bug.description}`}
              className="flex gap-3 rounded-lg border border-rose-400/20 bg-rose-500/10 p-3 text-sm"
            >
              <Bug aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-rose-300" />
              <div>
                <p className="font-medium text-rose-100">
                  {bug.description}{" "}
                  <span className="text-xs font-normal text-rose-200/80">({bug.severity} bug)</span>
                </p>
                <p className="text-xs text-rose-200/70">{bug.location}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
