import type { ReactNode } from "react";

import { Link } from "@/lib/router";
import { GRADE_PATH, preloadGradePage } from "@/lib/routes";

interface GradeLinkProps {
  className?: string;
  onNavigate?: () => void;
  children: ReactNode;
}

/** A link to the grading screen that starts loading it as soon as it is hovered or focused. */
export function GradeLink({ className, onNavigate, children }: GradeLinkProps) {
  return (
    <Link
      to={GRADE_PATH}
      onClick={onNavigate}
      onPointerEnter={preloadGradePage}
      onFocus={preloadGradePage}
      {...(className !== undefined && { className })}
    >
      {children}
    </Link>
  );
}
