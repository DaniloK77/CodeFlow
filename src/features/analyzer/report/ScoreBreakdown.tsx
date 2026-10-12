import { SEVERITY_STYLES } from "../grades";
import { type AnalysisReport, SEVERITIES } from "../schema";

interface Part {
  label: string;
  weight: number;
  score: number | null;
}

/** How the overall score was built: three weighted parts, plus a few size facts. */
export function ScoreBreakdown({ report }: { report: AnalysisReport }) {
  const { scores, weights } = report;
  const parts: Part[] = [
    { label: "Solves the task", weight: weights.task, score: scores.task },
    { label: "Code quality", weight: weights.quality, score: scores.quality },
    { label: "Explanation", weight: weights.explanation, score: scores.explanation },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <div className="space-y-3 rounded-xl border border-white/10 bg-white/5 p-4">
        {parts.map((part) => (
          <ScoreBar key={part.label} part={part} isGraded={report.verdict === "graded"} />
        ))}
      </div>
      <Stats report={report} />
    </div>
  );
}

function ScoreBar({ part, isGraded }: { part: Part; isGraded: boolean }) {
  const weight = isGraded ? `${part.weight}%` : `${part.weight}% once graded`;
  return (
    <div>
      <div className="mb-1 flex justify-between gap-2 text-sm">
        <span className="text-gray-300">
          {part.label} <span className="text-xs text-gray-500">({weight})</span>
        </span>
        <span className="font-semibold tabular-nums">
          {part.score === null ? "not verified" : `${part.score}/100`}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-white/10">
        <div
          className="h-full rounded-full bg-linear-to-r from-blue-500 to-cyan-400"
          style={{ width: `${part.score ?? 0}%` }}
        />
      </div>
    </div>
  );
}

function Stats({ report }: { report: AnalysisReport }) {
  const findings = report.quality.files.flatMap((file) => file.findings);
  const linesOfCode = report.quality.files.reduce((total, file) => total + file.codeLines, 0);
  return (
    <dl className="grid grid-cols-3 gap-2 rounded-xl border border-white/10 bg-white/5 p-4 text-center">
      <Stat label="Files" value={report.quality.files.length} />
      <Stat label="Lines of code" value={linesOfCode} />
      <Stat label="Graded in" value={formatDuration(report.durationMs)} />
      {SEVERITIES.map((severity) => (
        <Stat
          key={severity}
          label={SEVERITY_STYLES[severity].label}
          value={findings.filter((finding) => finding.severity === severity).length}
        />
      ))}
    </dl>
  );
}

function formatDuration(milliseconds: number): string {
  return milliseconds < 1000
    ? `${Math.max(1, Math.round(milliseconds))} ms`
    : `${(milliseconds / 1000).toFixed(1)} s`;
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div>
      <dt className="text-xs text-gray-400">{label}</dt>
      <dd className="text-lg font-semibold tabular-nums">
        {typeof value === "number" ? value.toLocaleString("en-US") : value}
      </dd>
    </div>
  );
}
