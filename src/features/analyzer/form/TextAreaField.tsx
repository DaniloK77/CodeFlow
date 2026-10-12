import { useId } from "react";

import { cn } from "@/lib/cn";

interface TextAreaFieldProps {
  step: number;
  label: string;
  hint: string;
  value: string;
  onChange: (value: string) => void;
  minChars: number;
  maxChars: number;
  placeholder: string;
  monospace?: boolean;
  rows?: number;
}

/** A numbered form step: label, hint, textarea and a character counter. */
export function TextAreaField({
  step,
  label,
  hint,
  value,
  onChange,
  minChars,
  maxChars,
  placeholder,
  monospace = false,
  rows = 4,
}: TextAreaFieldProps) {
  const id = useId();
  const length = value.trim().length;
  const isShort = length > 0 && length < minChars;

  return (
    <div className="space-y-2">
      <StepLabel step={step} htmlFor={id} label={label} />
      <p id={`${id}-hint`} className="text-xs text-gray-400">
        {hint}
      </p>
      <textarea
        id={id}
        value={value}
        rows={rows}
        maxLength={maxChars}
        aria-describedby={`${id}-hint ${id}-count`}
        spellCheck={!monospace}
        placeholder={placeholder}
        onChange={(event) => {
          onChange(event.target.value);
        }}
        className={cn(
          "w-full resize-y rounded-xl border border-white/10 bg-slate-900 p-3 text-sm leading-relaxed text-gray-100 placeholder:text-gray-500 focus:border-blue-400 focus:outline-none",
          monospace && "font-mono text-xs sm:text-sm",
        )}
      />
      <p id={`${id}-count`} className={cn("text-xs", isShort ? "text-amber-300" : "text-gray-500")}>
        {isShort
          ? `${minChars - length} more characters needed`
          : `${length.toLocaleString("en-US")} characters`}
      </p>
    </div>
  );
}

export function StepLabel({
  step,
  label,
  htmlFor,
}: {
  step: number;
  label: string;
  htmlFor?: string;
}) {
  const content = (
    <>
      <span
        aria-hidden="true"
        className="flex size-6 items-center justify-center rounded-full bg-blue-500/20 text-xs font-bold text-blue-200"
      >
        {step}
      </span>
      {label}
    </>
  );
  return htmlFor ? (
    <label htmlFor={htmlFor} className="flex items-center gap-2 text-sm font-semibold">
      {content}
    </label>
  ) : (
    <p className="flex items-center gap-2 text-sm font-semibold">{content}</p>
  );
}
