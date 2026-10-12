import { ClipboardPaste, FileArchive, FileCode } from "lucide-react";
import { useId, useState } from "react";

import { Tabs } from "@/components/ui/Tabs";
import { tabId, tabPanelId } from "@/lib/tabs";

import { LIMITS, SNIPPET_LANGUAGES } from "../constants";
import { Dropzone } from "../inputs/Dropzone";
import { FieldError } from "../inputs/FieldError";
import { FILE_RULES, type SolutionMode, type SubmissionDraft, validateFile } from "./submission";
import { StepLabel } from "./TextAreaField";

const MODES = [
  { id: "snippet", icon: ClipboardPaste, label: "Paste code" },
  { id: "file", icon: FileCode, label: "Single file" },
  { id: "archive", icon: FileArchive, label: "ZIP project" },
] as const satisfies readonly { id: SolutionMode; icon: unknown; label: string }[];

const TAB_ITEMS = MODES.map(({ id, icon: Icon, label }) => ({
  id,
  label: (
    <>
      <Icon aria-hidden="true" className="size-4" />
      {label}
    </>
  ),
}));

interface SolutionFieldProps {
  draft: SubmissionDraft;
  onChange: (changes: Partial<SubmissionDraft>) => void;
  disabled: boolean;
}

/** Step 2: the solution itself, pasted, as one file, or as a zipped project. */
export function SolutionField({ draft, onChange, disabled }: SolutionFieldProps) {
  const idPrefix = useId();
  const activeIndex = MODES.findIndex((mode) => mode.id === draft.mode);

  return (
    <div className="space-y-3">
      <StepLabel step={2} label="Your solution" />
      <Tabs
        label="How do you want to share your code?"
        variant="segmented"
        items={TAB_ITEMS}
        activeIndex={activeIndex}
        onSelect={(index) => {
          onChange({ mode: MODES[index]?.id ?? "snippet" });
        }}
        idPrefix={idPrefix}
      />
      <div role="tabpanel" id={tabPanelId(idPrefix)} aria-labelledby={tabId(idPrefix, draft.mode)}>
        {draft.mode === "snippet" && <CodeInput draft={draft} onChange={onChange} />}
        {draft.mode === "file" && (
          <FilePicker
            mode="file"
            file={draft.file}
            disabled={disabled}
            onFile={(file) => {
              onChange({ file });
            }}
          />
        )}
        {draft.mode === "archive" && (
          <FilePicker
            mode="archive"
            file={draft.archive}
            disabled={disabled}
            onFile={(archive) => {
              onChange({ archive });
            }}
          />
        )}
      </div>
    </div>
  );
}

const PICKER_COPY = {
  file: {
    accept: ".tsx,.ts,.jsx,.js,.py",
    title: "Drop a component or module here",
    hint: ".tsx, .ts, .jsx, .js or .py · up to 200 KB",
  },
  archive: {
    accept: ".zip,application/zip",
    title: "Drop your project .zip here",
    hint: "up to 5 MB · node_modules and build output are ignored · README, tests and CI count too",
  },
} as const;

interface FilePickerProps {
  mode: "file" | "archive";
  file: File | null;
  disabled: boolean;
  onFile: (file: File | null) => void;
}

function FilePicker({ mode, file, disabled, onFile }: FilePickerProps) {
  const [error, setError] = useState<string | null>(null);
  const copy = PICKER_COPY[mode];

  return (
    <div className="space-y-2">
      <Dropzone
        accept={copy.accept}
        title={copy.title}
        hint={copy.hint}
        file={file}
        disabled={disabled}
        onFile={(candidate) => {
          const problem = validateFile(candidate, FILE_RULES[mode]);
          setError(problem);
          onFile(problem ? null : candidate);
        }}
      />
      <FieldError message={error} />
    </div>
  );
}

function CodeInput({
  draft,
  onChange,
}: {
  draft: SubmissionDraft;
  onChange: (changes: Partial<SubmissionDraft>) => void;
}) {
  const id = useId();
  return (
    <div className="space-y-2">
      <label htmlFor={`${id}-code`} className="sr-only">
        Your code
      </label>
      <textarea
        id={`${id}-code`}
        value={draft.code}
        rows={10}
        spellCheck={false}
        placeholder="Paste a component, hook, module or Python script…"
        onChange={(event) => {
          onChange({ code: event.target.value });
        }}
        className="w-full resize-y rounded-xl border border-white/10 bg-slate-900 p-4 font-mono text-xs leading-relaxed text-gray-100 placeholder:text-gray-500 focus:border-blue-400 focus:outline-none sm:text-sm"
      />
      <div className="flex flex-wrap items-center justify-between gap-2 text-xs text-gray-500">
        <span>
          {draft.code.length.toLocaleString("en-US")} /{" "}
          {LIMITS.snippetChars.toLocaleString("en-US")} characters
        </span>
        <label className="flex items-center gap-2">
          Language
          <select
            value={draft.language}
            onChange={(event) => {
              const next = SNIPPET_LANGUAGES.find((option) => option.value === event.target.value);
              if (next) onChange({ language: next.value });
            }}
            className="rounded-lg border border-white/10 bg-slate-900 px-2 py-1 text-xs text-gray-200"
          >
            {SNIPPET_LANGUAGES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>
    </div>
  );
}
