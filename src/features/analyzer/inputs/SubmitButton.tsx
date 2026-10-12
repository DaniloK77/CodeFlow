import { LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";

interface SubmitButtonProps {
  isBusy: boolean;
  disabled?: boolean;
  children: ReactNode;
}

export function SubmitButton({ isBusy, disabled = false, children }: SubmitButtonProps) {
  return (
    <button
      type="submit"
      disabled={disabled || isBusy}
      className="flex w-full items-center justify-center gap-2 rounded-lg bg-linear-to-b from-blue-500 to-cyan-500 px-6 py-3 font-semibold transition-opacity disabled:cursor-not-allowed disabled:opacity-50 sm:w-auto"
    >
      {isBusy && <LoaderCircle aria-hidden="true" className="size-4 motion-safe:animate-spin" />}
      {isBusy ? "Analyzing…" : children}
    </button>
  );
}
