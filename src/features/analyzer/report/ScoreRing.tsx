import type { CSSProperties } from "react";

import { cn } from "@/lib/cn";
import { GRADE_STYLES } from "@/lib/grades";

import type { Grade } from "../schema";

const RADIUS = 52;
const CIRCUMFERENCE = 2 * Math.PI * RADIUS;

interface ScoreRingProps {
  score: number;
  /** The rank colours the ring. Without one (code quality alone) the ring stays neutral blue. */
  grade: Grade | null;
  label: string;
}

export function ScoreRing({ score, grade, label }: ScoreRingProps) {
  const offset = CIRCUMFERENCE * (1 - Math.min(Math.max(score, 0), 100) / 100);

  return (
    <div className="relative size-32 shrink-0 sm:size-36">
      <svg
        viewBox="0 0 120 120"
        role="img"
        aria-label={`${label} ${score} out of 100${grade ? `: ${grade}` : ""}`}
        className="size-full -rotate-90"
      >
        <circle cx="60" cy="60" r={RADIUS} strokeWidth="10" className="fill-none stroke-white/10" />
        <circle
          cx="60"
          cy="60"
          r={RADIUS}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          style={{ "--ring-circumference": CIRCUMFERENCE } as CSSProperties}
          className={cn(
            "fill-none motion-safe:animate-ring-fill",
            grade ? GRADE_STYLES[grade].stroke : "stroke-blue-400",
          )}
        />
      </svg>
      <div
        aria-hidden="true"
        className="absolute inset-0 flex flex-col items-center justify-center"
      >
        <span className="text-4xl font-bold tabular-nums">{score}</span>
        <span className="text-xs text-gray-400">/ 100</span>
      </div>
    </div>
  );
}
