import { CloudUpload } from "lucide-react";
import { type DragEvent, useId, useState } from "react";

import { cn } from "@/lib/cn";
import { formatBytes } from "@/lib/format";

interface DropzoneProps {
  accept: string;
  title: string;
  hint: string;
  file: File | null;
  disabled?: boolean;
  onFile: (file: File) => void;
}

/** Drag-and-drop file picker built on a real <input type="file">, so it stays keyboard-friendly. */
export function Dropzone({ accept, title, hint, file, disabled = false, onFile }: DropzoneProps) {
  const inputId = useId();
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    setIsDragging(false);
    const dropped = event.dataTransfer.files[0];
    if (dropped && !disabled) onFile(dropped);
  };

  return (
    // Drag-and-drop is a pointer-only shortcut; keyboard users get the native file input.
    <div
      role="presentation"
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => {
        setIsDragging(false);
      }}
      onDrop={handleDrop}
    >
      <label
        htmlFor={inputId}
        className={cn(
          "flex cursor-pointer flex-col items-center gap-2 rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors focus-within:border-blue-400",
          isDragging
            ? "border-blue-400 bg-blue-500/10"
            : "border-white/15 bg-white/5 hover:border-white/30",
        )}
      >
        <CloudUpload aria-hidden="true" className="mb-1 size-8 text-blue-300" />
        <span className="font-semibold break-all">{file ? file.name : title}</span>
        <span className="text-sm text-gray-400">
          {file ? `${formatBytes(file.size)} · choose another file` : hint}
        </span>
        <input
          id={inputId}
          type="file"
          accept={accept}
          disabled={disabled}
          className="sr-only"
          onChange={(event) => {
            const chosen = event.target.files?.[0];
            if (chosen) onFile(chosen);
            event.target.value = "";
          }}
        />
      </label>
    </div>
  );
}
