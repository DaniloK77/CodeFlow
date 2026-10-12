import { type RefObject, useEffect, useRef, useState } from "react";

import { PageShell } from "@/components/layout/PageShell";
import { GRADE_WEIGHTS } from "@/content/grading";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";
import { useMediaQuery } from "@/hooks/useMediaQuery";

import "./highlighting";
import { AttemptHistory } from "./AttemptHistory";
import { ErrorNotice } from "./ErrorNotice";
import { SubmissionForm } from "./form/SubmissionForm";
import {
  type Attempt,
  type Comparison,
  compareAttempts,
  findPrevious,
  useAttemptHistory,
} from "./history";
import { AnalysisReportView } from "./report/AnalysisReportView";
import { LoadingPanel, ReportPlaceholder } from "./ReportStates";
import { ServiceStatus } from "./ServiceStatus";
import { type AnalysisInput, type AnalysisState, useAnalysis } from "./useAnalysis";

const DESKTOP_QUERY = "(min-width: 1024px)";

const taskOf = (input: AnalysisInput) =>
  input.kind === "snippet" ? input.payload.task : input.assignment.task;

/** How the newest attempt differs from the one before it at the same task, if there was one. */
function compareWithPrevious(attempts: readonly Attempt[]): Comparison | null {
  const [latest, ...earlier] = attempts;
  const previous = latest ? findPrevious(earlier, latest) : undefined;
  return latest && previous ? compareAttempts(previous, latest) : null;
}

/** Moves focus to the report when a result arrives, and scrolls to it where it is below the form. */
function useRevealResult(reportRef: RefObject<HTMLElement | null>, state: AnalysisState): void {
  const isDesktop = useMediaQuery(DESKTOP_QUERY);
  const hasOutcome = state.status === "success" || state.status === "error";
  useEffect(() => {
    if (!hasOutcome) return;
    reportRef.current?.focus({ preventScroll: isDesktop });
    if (!isDesktop) reportRef.current?.scrollIntoView({ block: "start" });
  }, [hasOutcome, isDesktop, state, reportRef]);
}

/**
 * The grading screen: the submission form on the left, the report on the right. The form stays
 * filled after grading, so you can fix what the report found and grade again to see the change.
 */
export default function GradePage() {
  useDocumentTitle("Grade your solution · CodeFlow");
  const history = useAttemptHistory();
  const { state, run, reset } = useAnalysis((report, input) => {
    history.record(report, taskOf(input));
  });
  // Changing the key starts the form from scratch ("Start a new submission").
  const [formKey, setFormKey] = useState(0);
  const reportRef = useRef<HTMLElement>(null);
  useRevealResult(reportRef, state);
  const comparison = compareWithPrevious(history.attempts);

  return (
    <PageShell>
      <div className="mx-auto max-w-7xl px-4 pt-24 pb-16 sm:px-6 md:pt-32 lg:px-8">
        <header className="mb-8 max-w-3xl space-y-2">
          <h1 className="text-3xl font-semibold sm:text-4xl">Grade your solution</h1>
          <p className="text-gray-400">
            Task fit {GRADE_WEIGHTS.task}% · code quality {GRADE_WEIGHTS.quality}% · explanation{" "}
            {GRADE_WEIGHTS.explanation}%. Code quality is always scored; the rank needs the AI
            review.
          </p>
          <ServiceStatus />
        </header>

        <div className="grid grid-cols-1 items-start gap-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
          <section aria-label="Your submission">
            <SubmissionForm
              key={formKey}
              isBusy={state.status === "loading"}
              hasResult={state.status === "success"}
              onSubmit={(input) => void run(input)}
            />
          </section>

          <section
            ref={reportRef}
            tabIndex={-1}
            aria-label="Report"
            className="space-y-6 outline-none"
          >
            {state.status === "idle" && <ReportPlaceholder />}
            {state.status === "loading" && <LoadingPanel onCancel={reset} />}
            {state.status === "error" && <ErrorNotice error={state.error} />}
            {state.status === "success" && (
              <AnalysisReportView
                report={state.report}
                {...(state.input.kind === "snippet" && { code: state.input.payload.code })}
                comparison={comparison}
                onReset={() => {
                  reset();
                  setFormKey((key) => key + 1);
                }}
              />
            )}
            <AttemptHistory attempts={history.attempts} onClear={history.clear} />
          </section>
        </div>
      </div>
    </PageShell>
  );
}
