import type { GradeName } from "@/types/content";

interface GradeStyle {
  verdict: string;
  /** Accent text colour. */
  text: string;
  /** SVG stroke for score rings. */
  stroke: string;
  /** Bordered pill. */
  chip: string;
  /** Tinted card background. */
  surface: string;
}

// One palette per grade, shared by the hero preview and the analyzer report. Class names are
// written out in full so Tailwind's scanner can find them.
export const GRADE_STYLES: Record<GradeName, GradeStyle> = {
  Excellent: {
    verdict: "Clean, well-structured code that's ready for review.",
    text: "text-emerald-300",
    stroke: "stroke-emerald-400",
    chip: "border-emerald-400/30 bg-emerald-500/15 text-emerald-200",
    surface: "bg-emerald-500/15",
  },
  Good: {
    verdict: "Solid work, with a few things worth tidying up.",
    text: "text-amber-300",
    stroke: "stroke-amber-400",
    chip: "border-amber-400/30 bg-amber-500/15 text-amber-200",
    surface: "bg-amber-500/15",
  },
  Poor: {
    verdict: "Needs refactoring before it's ready for review.",
    text: "text-rose-300",
    stroke: "stroke-rose-400",
    chip: "border-rose-400/30 bg-rose-500/15 text-rose-200",
    surface: "bg-rose-500/15",
  },
};
