import { useEffect, useState } from "react";

import { cn } from "@/lib/cn";

import { fetchHealth } from "./api";
import type { Health } from "./schema";

type Status = { state: "checking" } | { state: "online"; health: Health } | { state: "offline" };

/** Live indicator: is the API up, and will task fit and explanation be graded by AI? */
export function ServiceStatus() {
  const [status, setStatus] = useState<Status>({ state: "checking" });

  useEffect(() => {
    const controller = new AbortController();
    fetchHealth(controller.signal).then(
      (health) => {
        setStatus({ state: "online", health });
      },
      () => {
        if (!controller.signal.aborted) setStatus({ state: "offline" });
      },
    );
    return () => {
      controller.abort();
    };
  }, []);

  return (
    <p role="status" className="flex items-center gap-2 text-xs text-gray-400">
      <span
        aria-hidden="true"
        className={cn(
          "size-2 rounded-full",
          status.state === "online" && "bg-emerald-400",
          status.state === "offline" && "bg-rose-400",
          status.state === "checking" && "bg-gray-500 motion-safe:animate-pulse",
        )}
      />
      {describe(status)}
    </p>
  );
}

function describe(status: Status): string {
  if (status.state === "checking") return "Checking service…";
  if (status.state === "offline") return "Grading service offline";
  const { ai_review: ai } = status.health;
  if (!ai.enabled) return "Online · AI review off: code quality only";
  return `Online · AI review on · ${ai.remaining_today} of ${ai.reviews_per_day} free reviews left today`;
}
