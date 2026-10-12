import { useState } from "react";

import type { FileReport } from "../schema";

const INITIAL_VISIBLE = 8;

/** Files ordered worst-first, so the review starts where it matters most. */
export function FileTable({ files }: { files: readonly FileReport[] }) {
  const [showAll, setShowAll] = useState(false);
  const ordered = [...files].sort((a, b) => a.score - b.score || a.path.localeCompare(b.path));
  const visible = showAll ? ordered : ordered.slice(0, INITIAL_VISIBLE);

  return (
    <div>
      <div className="overflow-x-auto rounded-xl border border-white/10">
        <table className="w-full text-left text-sm">
          <thead className="bg-white/5 text-xs text-gray-400">
            <tr>
              <th scope="col" className="px-4 py-2 font-medium">
                File
              </th>
              <th scope="col" className="px-4 py-2 text-right font-medium">
                LOC
              </th>
              <th scope="col" className="px-4 py-2 text-right font-medium">
                Max complexity
              </th>
              <th scope="col" className="px-4 py-2 text-right font-medium">
                Quality
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-white/5">
            {visible.map((file) => (
              <tr key={file.path}>
                <td className="px-4 py-2 font-mono text-xs break-all">{file.path}</td>
                <td className="px-4 py-2 text-right tabular-nums">{file.codeLines}</td>
                <td className="px-4 py-2 text-right tabular-nums">{file.maxComplexity}</td>
                <td className="px-4 py-2 text-right font-semibold tabular-nums">{file.score}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {files.length > INITIAL_VISIBLE && (
        <button
          type="button"
          onClick={() => {
            setShowAll((value) => !value);
          }}
          className="mt-3 text-sm text-blue-300 hover:text-blue-200"
        >
          {showAll ? "Show fewer files" : `Show all ${files.length} files`}
        </button>
      )}
    </div>
  );
}
