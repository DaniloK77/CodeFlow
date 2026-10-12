import { Info } from "lucide-react";

import type { AssignmentReview } from "../schema";

/** Why task fit and explanation weren't graded (AI off, allowance used up, or an error). */
export function ReviewNotice({ review }: { review: AssignmentReview }) {
  if (review.status === "completed" || !review.message) return null;
  return (
    <div className="flex gap-3 rounded-xl border border-amber-400/30 bg-amber-500/10 p-4 text-sm">
      <Info aria-hidden="true" className="size-5 shrink-0 text-amber-300" />
      <div>
        <p className="font-semibold text-amber-100">Task and explanation weren't graded</p>
        <p className="text-amber-100/80">{review.message}</p>
      </div>
    </div>
  );
}
