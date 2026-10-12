import { useState } from "react";

import { ASSIGNMENT_EXAMPLES } from "@/content/examples";
import type { AssignmentExample } from "@/types/content";

import { LIMITS } from "../constants";
import { SubmitButton } from "../inputs/SubmitButton";
import type { AnalysisInput } from "../useAnalysis";
import { SolutionField } from "./SolutionField";
import { draftProblems, EMPTY_DRAFT, type SubmissionDraft, toAnalysisInput } from "./submission";
import { TextAreaField } from "./TextAreaField";

interface SubmissionFormProps {
  isBusy: boolean;
  /** A report is on screen, so submitting again is a re-grade of an edited solution. */
  hasResult?: boolean;
  onSubmit: (input: AnalysisInput) => void;
}

/** Task → solution → explanation, then one button to grade all three together. */
export function SubmissionForm({ isBusy, hasResult = false, onSubmit }: SubmissionFormProps) {
  const [draft, setDraft] = useState<SubmissionDraft>(EMPTY_DRAFT);
  const [showProblems, setShowProblems] = useState(false);
  const problems = draftProblems(draft);
  const update = (changes: Partial<SubmissionDraft>) => {
    setDraft((current) => ({ ...current, ...changes }));
  };

  return (
    <form
      noValidate
      className="space-y-6"
      onSubmit={(event) => {
        event.preventDefault();
        if (problems.length > 0) {
          setShowProblems(true);
          return;
        }
        void toAnalysisInput(draft).then(onSubmit);
      }}
    >
      <ExamplePicker
        onPick={(example) => {
          setDraft(draftFromExample(example));
        }}
      />
      <TextAreaField
        step={1}
        label="The task"
        hint="Paste the assignment: what is the code supposed to do?"
        placeholder="Write a function that…"
        value={draft.task}
        onChange={(task) => {
          update({ task });
        }}
        minChars={LIMITS.taskMinChars}
        maxChars={LIMITS.textMaxChars}
      />
      <SolutionField draft={draft} onChange={update} disabled={isBusy} />
      <TextAreaField
        step={3}
        label="Your explanation"
        hint="How does your solution work? Describe your approach, key decisions and anything you'd improve."
        placeholder="I solved it by…"
        value={draft.explanation}
        onChange={(explanation) => {
          update({ explanation });
        }}
        minChars={LIMITS.explanationMinChars}
        maxChars={LIMITS.textMaxChars}
      />
      {showProblems && <ProblemList problems={problems} />}
      <SubmitButton isBusy={isBusy}>{hasResult ? "Grade again" : "Grade my solution"}</SubmitButton>
    </form>
  );
}

function ProblemList({ problems }: { problems: readonly string[] }) {
  if (problems.length === 0) return null;
  return (
    <ul role="alert" className="list-inside list-disc space-y-1 text-sm text-amber-200">
      {problems.map((problem) => (
        <li key={problem}>{problem}</li>
      ))}
    </ul>
  );
}

function draftFromExample(example: AssignmentExample): SubmissionDraft {
  return {
    ...EMPTY_DRAFT,
    task: example.task,
    explanation: example.explanation,
    mode: "snippet",
    code: example.code,
    language: example.language,
    filename: example.fileName,
  };
}

function ExamplePicker({ onPick }: { onPick: (example: AssignmentExample) => void }) {
  return (
    <div className="flex flex-wrap items-center gap-2 rounded-xl border border-white/10 bg-white/5 p-3 text-xs">
      <span className="text-gray-400">No assignment handy? Load an example:</span>
      {ASSIGNMENT_EXAMPLES.map((example) => (
        <button
          key={example.id}
          type="button"
          onClick={() => {
            onPick(example);
          }}
          className="rounded-full border border-white/10 bg-slate-900 px-3 py-1 text-gray-200 transition-colors hover:border-blue-400/40 hover:bg-blue-500/10"
        >
          {example.label}
        </button>
      ))}
    </div>
  );
}
