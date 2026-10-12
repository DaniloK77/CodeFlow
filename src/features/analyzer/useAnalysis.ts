import { useCallback, useEffect, useRef, useState } from "react";

import {
  AnalyzerApiError,
  type Assignment,
  reviewArchive,
  reviewSnippet,
  type SnippetPayload,
} from "./api";
import type { AnalysisReport } from "./schema";

export type AnalysisInput =
  | { kind: "archive"; file: File; assignment: Assignment }
  | { kind: "snippet"; payload: SnippetPayload };

export type AnalysisState =
  | { status: "idle" }
  | { status: "loading"; input: AnalysisInput }
  | { status: "success"; input: AnalysisInput; report: AnalysisReport }
  | { status: "error"; input: AnalysisInput; error: AnalyzerApiError };

/**
 * Request lifecycle for one analysis at a time. Starting a new run, cancelling or
 * unmounting aborts the in-flight request, so a stale response can never overwrite state.
 */
export function useAnalysis(onComplete?: (report: AnalysisReport, input: AnalysisInput) => void) {
  const [state, setState] = useState<AnalysisState>({ status: "idle" });
  const controllerRef = useRef<AbortController | null>(null);
  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  });

  const run = useCallback(async (input: AnalysisInput) => {
    controllerRef.current?.abort();
    const controller = new AbortController();
    controllerRef.current = controller;
    setState({ status: "loading", input });

    try {
      const report = await request(input, controller.signal);
      if (controller.signal.aborted) return;
      onCompleteRef.current?.(report, input);
      setState({ status: "success", input, report });
    } catch (error) {
      if (controller.signal.aborted) return;
      setState({ status: "error", input, error: toAnalyzerError(error) });
    }
  }, []);

  const reset = useCallback(() => {
    controllerRef.current?.abort();
    setState({ status: "idle" });
  }, []);

  useEffect(() => () => controllerRef.current?.abort(), []);

  return { state, run, reset };
}

function request(input: AnalysisInput, signal: AbortSignal): Promise<AnalysisReport> {
  return input.kind === "archive"
    ? reviewArchive(input.file, input.assignment, signal)
    : reviewSnippet(input.payload, signal);
}

function toAnalyzerError(error: unknown): AnalyzerApiError {
  if (error instanceof AnalyzerApiError) return error;
  return new AnalyzerApiError("Something went wrong while grading your solution.");
}
