import { CircleCheck } from "lucide-react";
import { useState } from "react";

import { SEVERITY_STYLES } from "../grades";
import { describeRule } from "../ruleDocs";
import type { Finding } from "../schema";
import { lineOf } from "./lines";
import { RichMessage } from "./RichMessage";

const INITIAL_VISIBLE = 12;

interface FindingsListProps {
  findings: readonly Finding[];
  /** Show "Line 7" instead of "path:7" when everything comes from one file. */
  singleFile?: boolean;
  /** When given, findings that point at a line get a "Show in code" button. */
  onShowInCode?: (line: number) => void;
}

export function FindingsList({ findings, singleFile = false, onShowInCode }: FindingsListProps) {
  const [showAll, setShowAll] = useState(false);

  if (findings.length === 0) {
    return (
      <p className="flex items-center gap-2 rounded-xl border border-emerald-400/20 bg-emerald-500/10 p-4 text-sm text-emerald-200">
        <CircleCheck aria-hidden="true" className="size-5" />
        No findings: nothing to fix here.
      </p>
    );
  }

  const visible = showAll ? findings : findings.slice(0, INITIAL_VISIBLE);
  return (
    <div>
      <ul className="divide-y divide-white/5 rounded-xl border border-white/10 bg-white/5">
        {visible.map((finding, index) => (
          <FindingItem
            key={`${finding.path}:${finding.line}:${finding.rule}:${index}`}
            finding={finding}
            singleFile={singleFile}
            {...(onShowInCode && { onShowInCode })}
          />
        ))}
      </ul>
      {findings.length > INITIAL_VISIBLE && (
        <button
          type="button"
          onClick={() => {
            setShowAll((value) => !value);
          }}
          className="mt-3 text-sm text-blue-300 hover:text-blue-200"
        >
          {showAll ? "Show fewer" : `Show all ${findings.length} findings`}
        </button>
      )}
    </div>
  );
}

interface FindingItemProps {
  finding: Finding;
  singleFile: boolean;
  onShowInCode?: (line: number) => void;
}

function FindingItem({ finding, singleFile, onShowInCode }: FindingItemProps) {
  const doc = describeRule(finding.rule);
  const line = lineOf(finding);
  const location = singleFile ? `Line ${finding.line}` : `${finding.path}:${finding.line}`;

  return (
    <li className="flex gap-3 p-4">
      <span
        aria-hidden="true"
        className={`mt-1.5 size-2 shrink-0 rounded-full ${SEVERITY_STYLES[finding.severity].dot}`}
      />
      <div className="min-w-0 space-y-1 text-sm">
        <p className="flex flex-wrap items-baseline gap-x-2">
          <span className="font-semibold">{doc.title}</span>
          <span className="sr-only">({finding.severity})</span>
          {onShowInCode && line !== null ? (
            <button
              type="button"
              onClick={() => {
                onShowInCode(line);
              }}
              aria-label={`Show line ${line} in the code: ${doc.title}`}
              className="rounded font-mono text-xs break-all text-blue-300 underline-offset-2 hover:text-blue-200 hover:underline"
            >
              {location}
            </button>
          ) : (
            <span className="font-mono text-xs break-all text-gray-400">{location}</span>
          )}
        </p>
        <p className="text-gray-300">
          <RichMessage text={finding.message} />
        </p>
        {doc.why && <p className="text-xs text-gray-500">{doc.why}</p>}
      </div>
    </li>
  );
}
