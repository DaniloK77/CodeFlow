import type { NavLink } from "@/types/content";

export const SITE_NAME = "CodeFlow";

export const SITE_TAGLINE =
  "Code review for students and junior developers: does your code solve the task, how well is it written, and can you explain it?";

export const REPOSITORY_URL = "https://github.com/DaniloK77/CodeFlow-UI-";

/** Sections of the landing page; each `href` must match a section `id` (see App.test.tsx). */
export const NAV_LINKS: readonly NavLink[] = [
  { label: "How it works", href: "/#features" },
  { label: "Grading", href: "/#grading" },
  { label: "Rules", href: "/#rules" },
  { label: "Pricing", href: "/#pricing" },
];
