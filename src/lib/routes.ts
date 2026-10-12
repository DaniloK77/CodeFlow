export const HOME_PATH = "/";
export const GRADE_PATH = "/grade";

export const loadGradePage = () => import("@/features/analyzer/GradePage");

/** Starts downloading the grading screen early, e.g. while the pointer is over a link to it. */
export function preloadGradePage(): void {
  void loadGradePage();
}
