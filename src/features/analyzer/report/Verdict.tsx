import type { ReactNode } from "react";

import { GRADE_STYLES } from "@/lib/grades";

import type { AnalysisReport } from "../schema";
import { ScoreRing } from "./ScoreRing";

/**
 * The headline. A fully graded submission gets a rank. Without a completed AI review there is
 * only a code-quality score, and the report says the task was not verified.
 */
export function Verdict({ report }: { report: AnalysisReport }) {
  if (report.grade !== null && report.overallScore !== null) {
    const style = GRADE_STYLES[report.grade];
    return (
      <VerdictLayout
        ring={<ScoreRing score={report.overallScore} grade={report.grade} label="Overall score" />}
        name={report.name}
      >
        <p className={`text-4xl font-bold tracking-tight sm:text-5xl ${style.text}`}>
          {report.grade}
        </p>
        <p className="text-gray-300">{report.review.summary ?? style.verdict}</p>
      </VerdictLayout>
    );
  }

  return (
    <VerdictLayout
      ring={<ScoreRing score={report.quality.score} grade={null} label="Code quality" />}
      name={report.name}
    >
      <p className="text-3xl font-bold tracking-tight sm:text-4xl">
        Code quality <span className="text-blue-300 tabular-nums">{report.quality.score}/100</span>
      </p>
      <p>
        <span className="rounded-full border border-amber-400/30 bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-200">
          Task not verified
        </span>
      </p>
      <p className="text-gray-300">
        No rank without an AI review of the task: clean code can still solve the wrong problem.
      </p>
    </VerdictLayout>
  );
}

function VerdictLayout({
  ring,
  name,
  children,
}: {
  ring: ReactNode;
  name: string;
  children: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-6 text-center sm:flex-row sm:text-left">
      {ring}
      <div className="space-y-2">
        <p className="text-sm break-all text-gray-400">{name}</p>
        {children}
      </div>
    </div>
  );
}
