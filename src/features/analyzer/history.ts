import { useCallback, useState } from "react";
import { z } from "zod";

import { type AnalysisReport, GRADES, SEVERITIES } from "./schema";

// Attempt history lives in this browser's localStorage only. Nothing is sent anywhere, and every
// read and write is guarded: storage can be full, blocked or full of data from an older version.

const STORAGE_KEY = "codeflow.attempts.v1";
export const MAX_ATTEMPTS = 20;
const MAX_FINDINGS_PER_ATTEMPT = 200;
const TASK_KEY_LENGTH = 120;

const attemptSchema = z.object({
  id: z.string(),
  at: z.number(),
  name: z.string(),
  taskKey: z.string(),
  quality: z.number(),
  overall: z.number().nullable(),
  grade: z.enum(GRADES).nullable(),
  findings: z.array(
    z.object({ rule: z.string(), severity: z.enum(SEVERITIES), message: z.string() }),
  ),
});

export type Attempt = z.infer<typeof attemptSchema>;

/** Attempts at the same task and file are compared with each other. */
export function taskKeyFor(task: string, name: string): string {
  const normalised = task.toLowerCase().replace(/\s+/g, " ").trim().slice(0, TASK_KEY_LENGTH);
  return `${name}::${normalised}`;
}

export function toAttempt(report: AnalysisReport, task: string, now = Date.now()): Attempt {
  const findings = report.quality.files
    .flatMap((file) => file.findings)
    .slice(0, MAX_FINDINGS_PER_ATTEMPT)
    .map(({ rule, severity, message }) => ({ rule, severity, message }));
  return {
    id: `${now}-${Math.random().toString(36).slice(2, 8)}`,
    at: now,
    name: report.name,
    taskKey: taskKeyFor(task, report.name),
    quality: report.quality.score,
    overall: report.overallScore,
    grade: report.grade,
    findings,
  };
}

export function readAttempts(storage?: Storage): Attempt[] {
  try {
    const raw = (storage ?? window.localStorage).getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = z.array(attemptSchema).safeParse(JSON.parse(raw));
    return parsed.success ? parsed.data.slice(0, MAX_ATTEMPTS) : [];
  } catch {
    return [];
  }
}

export function writeAttempts(attempts: readonly Attempt[], storage?: Storage): void {
  try {
    (storage ?? window.localStorage).setItem(STORAGE_KEY, JSON.stringify(attempts));
  } catch {
    // The history is a convenience; losing it must never break grading.
  }
}

/** The latest earlier attempt at the same task and file. `attempts` is newest first. */
export function findPrevious(attempts: readonly Attempt[], current: Attempt): Attempt | undefined {
  return attempts.find(
    (attempt) => attempt.id !== current.id && attempt.taskKey === current.taskKey,
  );
}

export interface RuleChange {
  rule: string;
  /** How many findings of the rule disappeared (negative) or appeared (positive). */
  change: number;
}

export interface Comparison {
  previous: Attempt;
  qualityDelta: number;
  overallDelta: number | null;
  resolved: RuleChange[];
  added: RuleChange[];
}

function countByRule(attempt: Attempt): Map<string, number> {
  const counts = new Map<string, number>();
  for (const { rule } of attempt.findings) counts.set(rule, (counts.get(rule) ?? 0) + 1);
  return counts;
}

/** What changed from `previous` to `current`, rule by rule (messages shift as code changes). */
export function compareAttempts(previous: Attempt, current: Attempt): Comparison {
  const before = countByRule(previous);
  const after = countByRule(current);
  const changes = [...new Set([...before.keys(), ...after.keys()])]
    .map((rule) => ({ rule, change: (after.get(rule) ?? 0) - (before.get(rule) ?? 0) }))
    .filter(({ change }) => change !== 0)
    .sort((a, b) => a.rule.localeCompare(b.rule));
  return {
    previous,
    qualityDelta: current.quality - previous.quality,
    overallDelta:
      current.overall !== null && previous.overall !== null
        ? current.overall - previous.overall
        : null,
    resolved: changes.filter(({ change }) => change < 0),
    added: changes.filter(({ change }) => change > 0),
  };
}

export interface AttemptHistory {
  attempts: readonly Attempt[];
  record: (report: AnalysisReport, task: string) => void;
  clear: () => void;
}

export function useAttemptHistory(): AttemptHistory {
  const [attempts, setAttempts] = useState<readonly Attempt[]>(() => readAttempts());

  const record = useCallback((report: AnalysisReport, task: string) => {
    setAttempts((current) => {
      const next = [toAttempt(report, task), ...current].slice(0, MAX_ATTEMPTS);
      writeAttempts(next);
      return next;
    });
  }, []);

  const clear = useCallback(() => {
    setAttempts([]);
    writeAttempts([]);
  }, []);

  return { attempts, record, clear };
}
