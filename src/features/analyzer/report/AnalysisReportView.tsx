import { Download, RotateCcw } from "lucide-react";
import { type ReactNode, useState } from "react";

import type { Comparison } from "../history";
import type { AnalysisReport } from "../schema";
import { AttemptComparison } from "./AttemptComparison";
import { CodeView } from "./CodeView";
import { downloadReport } from "./download";
import { ExplanationReview } from "./ExplanationReview";
import { FileTable } from "./FileTable";
import { FindingsList } from "./FindingsList";
import { HygieneList } from "./HygieneList";
import { type ActiveLine, lineAnchorId } from "./lines";
import { MentorFeedback } from "./MentorFeedback";
import { QualityBreakdown } from "./QualityBreakdown";
import { ReviewNotice } from "./ReviewNotice";
import { ScoreBreakdown } from "./ScoreBreakdown";
import { StaticChecks } from "./StaticChecks";
import { TaskChecklist } from "./TaskChecklist";
import { Verdict } from "./Verdict";

interface AnalysisReportViewProps {
  report: AnalysisReport;
  /** The submitted snippet; shown with flagged lines when present. */
  code?: string;
  /** How this attempt differs from the previous one at the same task, if there was one. */
  comparison?: Comparison | null;
  onReset: () => void;
}

export function AnalysisReportView({ report, code, comparison, onReset }: AnalysisReportViewProps) {
  const { review, quality } = report;
  const isReviewed = review.status === "completed";

  return (
    <div className="space-y-8">
      <Verdict report={report} />
      <ReviewNotice review={review} />
      {comparison && <AttemptComparison comparison={comparison} currentQuality={quality.score} />}
      <ScoreBreakdown report={report} />

      {report.checks.length > 0 && (
        <ReportSection
          title={isReviewed ? "Names checked against your code" : "What we could verify without AI"}
        >
          <StaticChecks checks={report.checks} />
        </ReportSection>
      )}
      {isReviewed && (
        <ReportSection title={`Does it solve the task? ${report.scores.task ?? 0}/100`}>
          <TaskChecklist review={review} />
        </ReportSection>
      )}
      {isReviewed && review.explanation && (
        <ReportSection title={`Your explanation ${report.scores.explanation ?? 0}/100`}>
          <ExplanationReview assessment={review.explanation} />
        </ReportSection>
      )}
      {isReviewed && (
        <ReportSection title="Mentor feedback">
          <MentorFeedback review={review} />
        </ReportSection>
      )}

      <ReportSection title={`Code quality ${quality.score}/100`}>
        <QualityDetails report={report} code={code} />
      </ReportSection>

      <Actions report={report} onReset={onReset} />
    </div>
  );
}

function QualityDetails({ report, code }: { report: AnalysisReport; code: string | undefined }) {
  const { quality } = report;
  const [activeLine, setActiveLine] = useState<ActiveLine | null>(null);
  const findings = quality.files.flatMap((file) => file.findings);
  const [firstFile] = quality.files;
  const isArchive = report.source === "archive";
  const canShowCode = code !== undefined && firstFile !== undefined;

  const showInCode = (line: number) => {
    setActiveLine((current) => ({ line, nonce: (current?.nonce ?? 0) + 1 }));
    document
      .getElementById(lineAnchorId(line))
      ?.scrollIntoView({ block: "center", behavior: "smooth" });
  };

  return (
    <div className="space-y-6">
      <QualityBreakdown quality={quality} />
      {canShowCode && (
        <CodeView
          code={code}
          path={firstFile.path}
          findings={firstFile.findings}
          activeLine={activeLine}
        />
      )}
      {isArchive && <FileTable files={quality.files} />}
      <FindingsList
        findings={findings}
        singleFile={!isArchive}
        {...(canShowCode && { onShowInCode: showInCode })}
      />
      {isArchive && <HygieneList checks={quality.hygiene} />}
      {report.skipped.length > 0 && <SkippedFiles skipped={report.skipped} />}
    </div>
  );
}

const SECONDARY_BUTTON =
  "flex items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-4 py-2.5 text-sm font-medium transition-colors hover:bg-white/10";

function Actions({ report, onReset }: { report: AnalysisReport; onReset: () => void }) {
  return (
    <div className="flex flex-col gap-3 border-t border-white/10 pt-6 sm:flex-row">
      <button type="button" onClick={onReset} className={SECONDARY_BUTTON}>
        <RotateCcw aria-hidden="true" className="size-4" />
        Start a new submission
      </button>
      <button
        type="button"
        onClick={() => {
          downloadReport(report);
        }}
        className={SECONDARY_BUTTON}
      >
        <Download aria-hidden="true" className="size-4" />
        Download JSON report
      </button>
    </div>
  );
}

function ReportSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h3 className="mb-3 text-sm font-semibold tracking-wide text-gray-400 uppercase">{title}</h3>
      {children}
    </section>
  );
}

function SkippedFiles({ skipped }: { skipped: AnalysisReport["skipped"] }) {
  return (
    <details className="rounded-xl border border-white/10 bg-white/5 p-4 text-sm">
      <summary className="cursor-pointer text-gray-300">
        {skipped.length} file{skipped.length === 1 ? " was" : "s were"} skipped
      </summary>
      <ul className="mt-3 space-y-1 font-mono text-xs text-gray-400">
        {skipped.map((item) => (
          <li key={`${item.path}:${item.reason}`}>
            {item.path}: {item.reason}
          </li>
        ))}
      </ul>
    </details>
  );
}
