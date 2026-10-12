import { lazy, Suspense } from "react";

import { GRADE_PATH, loadGradePage } from "@/lib/routes";
import { usePathname } from "@/lib/navigation";

import { LandingPage } from "./pages/LandingPage";

// Code-split: the grading screen (validation, highlighting, history) is only downloaded when
// a visitor opens it.
const GradePage = lazy(loadGradePage);

export function App() {
  const pathname = usePathname();
  if (pathname.replace(/\/$/, "") === GRADE_PATH) {
    return (
      <Suspense fallback={<div className="min-h-screen bg-slate-950" aria-busy="true" />}>
        <GradePage />
      </Suspense>
    );
  }
  return <LandingPage />;
}
