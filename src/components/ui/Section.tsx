import type { ReactNode } from "react";

import { cn } from "@/lib/cn";

interface SectionProps {
  id: string;
  /** Id of the heading that names this landmark for assistive tech. */
  labelledBy: string;
  children: ReactNode;
  narrow?: boolean;
}

export function Section({ id, labelledBy, children, narrow = false }: SectionProps) {
  return (
    <section
      id={id}
      aria-labelledby={labelledBy}
      className="relative px-4 py-16 sm:px-6 sm:py-20 lg:px-8"
    >
      <div className={cn("mx-auto", narrow ? "max-w-6xl" : "max-w-7xl")}>{children}</div>
    </section>
  );
}
