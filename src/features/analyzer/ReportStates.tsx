import { Gauge, ListChecks, LoaderCircle, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";

const STEPS = [
  "Checking that it is code we can grade",
  "Running the static analysis",
  "Asking the AI reviewer about the task and your explanation (can take up to a minute)",
] as const;

/** Shown while a request is in flight. We can't know the progress, so it says what happens. */
export function LoadingPanel({ onCancel }: { onCancel: () => void }) {
  const [seconds, setSeconds] = useState(0);
  useEffect(() => {
    const timer = window.setInterval(() => {
      setSeconds((value) => value + 1);
    }, 1000);
    return () => {
      window.clearInterval(timer);
    };
  }, []);

  return (
    <div
      role="status"
      aria-label="Grading progress"
      className="space-y-5 rounded-2xl border border-white/10 bg-white/5 p-6"
    >
      <p className="flex items-center gap-3 text-lg font-semibold">
        <LoaderCircle
          aria-hidden="true"
          className="size-5 text-blue-300 motion-safe:animate-spin"
        />
        Grading your solution…
        <span className="ml-auto text-sm font-normal text-gray-400 tabular-nums">{seconds} s</span>
      </p>
      <ol className="list-inside list-decimal space-y-2 text-sm text-gray-300">
        {STEPS.map((step) => (
          <li key={step}>{step}</li>
        ))}
      </ol>
      <button
        type="button"
        onClick={onCancel}
        className="rounded-lg border border-white/10 px-4 py-2 text-sm transition-colors hover:bg-white/10"
      >
        Cancel
      </button>
    </div>
  );
}

const PROMISES = [
  {
    icon: Gauge,
    title: "A strict quality score",
    text: "0–100 across six dimensions, with every lost point explained. Typical clean-looking code lands between 60 and 75.",
  },
  {
    icon: ListChecks,
    title: "Your task, checked against the code",
    text: "Functions and components your task names are looked up in the code, with or without AI.",
  },
  {
    icon: ShieldCheck,
    title: "No fake ranks",
    text: "Excellent, Good or Poor only when the AI has verified the task. Otherwise you get the score and an honest “task not verified”.",
  },
] as const;

/** Shown before the first submission, so the right-hand side is never an empty box. */
export function ReportPlaceholder() {
  return (
    <div className="space-y-4 rounded-2xl border border-dashed border-white/15 p-6">
      <h2 className="text-lg font-semibold">Your report will appear here</h2>
      <ul className="space-y-4">
        {PROMISES.map(({ icon: Icon, title, text }) => (
          <li key={title} className="flex gap-3">
            <Icon aria-hidden="true" className="mt-0.5 size-5 shrink-0 text-blue-300" />
            <div>
              <p className="text-sm font-medium">{title}</p>
              <p className="text-sm text-gray-400">{text}</p>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
