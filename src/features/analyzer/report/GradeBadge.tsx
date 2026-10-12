import { cn } from "@/lib/cn";
import { GRADE_STYLES } from "@/lib/grades";

import type { Grade } from "../schema";

export function GradeBadge({ grade, className }: { grade: Grade; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-wide",
        GRADE_STYLES[grade].chip,
        className,
      )}
    >
      {grade}
    </span>
  );
}
