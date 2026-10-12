import { ArrowRight, Plus } from "lucide-react";

import type { AssignmentReview } from "../schema";

/** What went well and what to do next, written for a learner. */
export function MentorFeedback({ review }: { review: AssignmentReview }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <FeedbackList title="What went well" items={review.strengths} icon="plus" />
      <FeedbackList title="What to improve next" items={review.improvements} icon="arrow" />
    </div>
  );
}

function FeedbackList({
  title,
  items,
  icon,
}: {
  title: string;
  items: readonly string[];
  icon: "plus" | "arrow";
}) {
  const Icon = icon === "plus" ? Plus : ArrowRight;
  const colour = icon === "plus" ? "text-emerald-400" : "text-blue-300";
  return (
    <div className="rounded-xl border border-white/10 bg-white/5 p-4">
      <h4 className="mb-2 text-sm font-semibold">{title}</h4>
      {items.length === 0 ? (
        <p className="text-sm text-gray-500">Nothing to add.</p>
      ) : (
        <ul className="space-y-2 text-sm text-gray-300">
          {items.map((item) => (
            <li key={item} className="flex gap-2">
              <Icon aria-hidden="true" className={`mt-0.5 size-4 shrink-0 ${colour}`} />
              {item}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
