import { ScanSearch } from "lucide-react";
import { useId, useState } from "react";

import { CodeBlock } from "@/components/ui/CodeBlock";
import { Tabs } from "@/components/ui/Tabs";
import { WindowControls } from "@/components/ui/WindowControls";
import { EXAMPLE_REPORTS } from "@/content/exampleReports";
import { lineOf } from "@/lib/findings";
import { languageForPath } from "@/lib/languages";
import { tabId, tabPanelId } from "@/lib/tabs";
import type { AssignmentExample, ExampleReport } from "@/types/content";

import { HighlightCard } from "./HighlightCard";

const CODE_STYLE = {
  height: "100%",
  padding: "0.75rem",
  borderRadius: "8px",
  border: "1px solid #3c3c3c",
  fontSize: "11px",
  lineHeight: "1.4",
  whiteSpace: "pre-wrap",
  scrollbarWidth: "thin",
} as const;

/** A review window: switch between example submissions to see each task, its code and grade. */
export function CodePreview({ samples }: { samples: readonly AssignmentExample[] }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const idPrefix = useId();

  const active = samples[activeIndex];
  if (!active) return null;

  const tabs = samples.map((sample) => ({ id: sample.fileName, label: sample.fileName }));
  const report = EXAMPLE_REPORTS[active.id];
  const flagged = flaggedLines(report);

  return (
    <div className="relative w-full">
      <div className="relative rounded-xl border border-white/10 bg-white/5 p-3 shadow-2xl backdrop-blur-xl sm:rounded-2xl sm:p-4">
        <div className="flex h-70 flex-col overflow-hidden rounded-lg border border-white/5 bg-linear-to-br from-gray-900/20 to-gray-800/20 backdrop-blur-sm sm:h-87.5 lg:h-112.5">
          <TitleBar />
          <div className="flex min-h-0 grow flex-col p-3 sm:p-4">
            <Tabs
              label="Example files"
              items={tabs}
              activeIndex={activeIndex}
              onSelect={setActiveIndex}
              idPrefix={idPrefix}
            />
            <p className="mb-2 line-clamp-2 text-left text-xs text-gray-400">
              <span className="font-semibold text-gray-300">Task:</span> {active.task}
            </p>
            <div
              role="tabpanel"
              id={tabPanelId(idPrefix)}
              aria-labelledby={tabId(idPrefix, active.fileName)}
              tabIndex={0}
              className="min-h-0 grow rounded-lg"
            >
              <CodeBlock
                language={languageForPath(active.fileName)}
                code={active.code}
                style={CODE_STYLE}
                getLineProps={(line) => ({
                  className: flagged.has(line) ? "block bg-amber-500/15" : "block",
                })}
              />
            </div>
          </div>
        </div>

        {report && <HighlightCard report={report} />}
      </div>
    </div>
  );
}

function TitleBar() {
  return (
    <div className="flex items-center justify-between border-b border-white/10 bg-white/5 px-3 py-2 sm:px-4 sm:py-3">
      <div className="flex items-center gap-2">
        <WindowControls />
        <span className="text-xs text-gray-300 sm:text-sm">CodeFlow Review</span>
      </div>
      <ScanSearch aria-hidden="true" className="size-3 text-gray-400 sm:size-4" />
    </div>
  );
}

/** Lines the real analysis flagged, tinted in the preview so the findings can be seen in place. */
function flaggedLines(report: ExampleReport | undefined): Set<number> {
  const lines = new Set<number>();
  for (const finding of report?.findings ?? []) {
    const line = lineOf(finding);
    if (line !== null) lines.add(line);
  }
  return lines;
}
