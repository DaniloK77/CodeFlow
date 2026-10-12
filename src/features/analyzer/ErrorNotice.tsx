import { FileQuestion, TriangleAlert, WifiOff } from "lucide-react";

import type { AnalyzerApiError } from "./api";

interface Description {
  title: string;
  hint: string;
}

const SUPPORTED = "CodeFlow grades JavaScript, TypeScript (including React) and Python.";

/** Reasons the grader gives for turning input down (see ErrorResponse in api/schemas.py). */
const REFUSALS: Readonly<Record<string, (message: string) => Description>> = {
  not_code: (message) => ({
    title: "That doesn't look like code",
    hint: `${message} Paste the function, component or script you wrote.`,
  }),
  unsupported_language: (message) => ({
    title: "That language isn't supported yet",
    hint: `${message} ${SUPPORTED}`,
  }),
  too_little_code: (message) => ({
    title: "There isn't enough code to grade",
    hint: `${message} Paste the whole solution, not a line or two.`,
  }),
  analysis_timeout: (message) => ({
    title: "That took too long to analyse",
    hint: message,
  }),
};

function describe(error: AnalyzerApiError): Description {
  const refusal = error.code ? REFUSALS[error.code] : undefined;
  if (refusal) return refusal(error.message);
  if (error.status === null) {
    return {
      title: "The grading service is offline",
      hint: "Run `npm run dev` to start the web app and the API together, then try again.",
    };
  }
  if (error.status === 429) {
    const wait = error.retryAfterSeconds ? ` in ${error.retryAfterSeconds} s` : " in a moment";
    return { title: "Too many requests", hint: `Please try again${wait}.` };
  }
  if (error.status === 503) {
    return { title: "The grader is busy", hint: "Please try again in a few seconds." };
  }
  if (error.status === 413) {
    return { title: "That's too big for the free plan", hint: error.message };
  }
  return { title: "We couldn't grade that", hint: error.message };
}

const ICON_CLASSES = "size-5 shrink-0 text-rose-300";

function ErrorIcon({ error }: { error: AnalyzerApiError }) {
  if (error.status === null) return <WifiOff aria-hidden="true" className={ICON_CLASSES} />;
  const Icon = error.code ? FileQuestion : TriangleAlert;
  return <Icon aria-hidden="true" className={ICON_CLASSES} />;
}

export function ErrorNotice({ error }: { error: AnalyzerApiError }) {
  const { title, hint } = describe(error);

  return (
    <div
      role="alert"
      className="flex gap-3 rounded-xl border border-rose-400/30 bg-rose-500/10 p-4 text-sm"
    >
      <ErrorIcon error={error} />
      <div>
        <p className="font-semibold text-rose-100">{title}</p>
        <p className="text-rose-200/80">{hint}</p>
      </div>
    </div>
  );
}
