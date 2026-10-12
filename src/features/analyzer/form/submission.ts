import type { SnippetLanguage } from "../constants";
import { ARCHIVE_EXTENSIONS, LIMITS, SOURCE_EXTENSIONS } from "../constants";
import type { AnalysisInput } from "../useAnalysis";
import { validateFile } from "../validation";

export type SolutionMode = "archive" | "snippet" | "file";

/** Everything the submission form holds. */
export interface SubmissionDraft {
  task: string;
  explanation: string;
  mode: SolutionMode;
  archive: File | null;
  code: string;
  language: SnippetLanguage;
  /** Original file name of pasted code, when known (examples have one). */
  filename: string;
  file: File | null;
}

export const EMPTY_DRAFT: SubmissionDraft = {
  task: "",
  explanation: "",
  mode: "snippet",
  archive: null,
  code: "",
  language: "auto",
  filename: "",
  file: null,
};

/** What still stops the draft from being submitted, in reading order. Empty when ready. */
export function draftProblems(draft: SubmissionDraft): string[] {
  const problems: string[] = [];
  if (draft.task.trim().length < LIMITS.taskMinChars) {
    problems.push(`Describe the task (at least ${LIMITS.taskMinChars} characters).`);
  }
  problems.push(...solutionProblems(draft));
  if (draft.explanation.trim().length < LIMITS.explanationMinChars) {
    problems.push(`Explain your solution (at least ${LIMITS.explanationMinChars} characters).`);
  }
  return problems;
}

function solutionProblems(draft: SubmissionDraft): string[] {
  switch (draft.mode) {
    case "archive":
      return draft.archive ? [] : ["Choose a .zip of your project."];
    case "file":
      return draft.file ? [] : ["Choose a source file."];
    case "snippet": {
      if (!draft.code.trim()) return ["Paste your code."];
      if (draft.code.length > LIMITS.snippetChars) {
        return [`Your code is over ${LIMITS.snippetChars.toLocaleString("en-US")} characters.`];
      }
      return [];
    }
  }
}

/** Rules a picked file must pass in each upload mode. */
export const FILE_RULES = {
  archive: { maxBytes: LIMITS.archiveBytes, extensions: ARCHIVE_EXTENSIONS },
  file: { maxBytes: LIMITS.sourceFileBytes, extensions: SOURCE_EXTENSIONS },
} as const;

export { validateFile };

/** Turns a ready draft into an API request (reading a single file's text when needed). */
export async function toAnalysisInput(draft: SubmissionDraft): Promise<AnalysisInput> {
  const assignment = { task: draft.task.trim(), explanation: draft.explanation.trim() };
  if (draft.mode === "archive" && draft.archive) {
    return { kind: "archive", file: draft.archive, assignment };
  }
  if (draft.mode === "file" && draft.file) {
    const code = await draft.file.text();
    return {
      kind: "snippet",
      payload: { ...assignment, code, language: "auto", filename: draft.file.name },
    };
  }
  const payload = { ...assignment, code: draft.code, language: draft.language };
  return {
    kind: "snippet",
    payload: draft.filename ? { ...payload, filename: draft.filename } : payload,
  };
}
