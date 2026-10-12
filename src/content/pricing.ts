import type { PricingPlan } from "@/types/content";

import { REPOSITORY_URL } from "./site";

/** Where interest in the planned plans is collected: the project's public issue tracker. */
export const PLANNED_PLANS_HREF = `${REPOSITORY_URL}/issues/new?title=Interest%20in%20a%20paid%20plan`;

export const PRICING_PLANS: readonly PricingPlan[] = [
  {
    id: "free",
    name: "Free",
    monthlyPrice: 0,
    status: "available",
    description: "For learners trying it out, no sign-up",
    features: [
      "5 AI reviews a day",
      "Unlimited code-quality checks",
      "Paste code, drop a file or upload a .zip",
      "Requirement checklist and mentor feedback",
      "Attempt history with before/after comparison",
      "Downloadable JSON report",
    ],
    cta: { kind: "analyzer", label: "Grade my solution" },
  },
  {
    id: "pro",
    name: "Pro",
    monthlyPrice: 20,
    status: "planned",
    description: "For students and junior developers who practise every day",
    features: [
      "Everything in Free",
      "100 AI reviews a month",
      "Grade history synced across devices",
      "Private GitHub repositories",
      "Projects up to 50 MB",
    ],
    cta: { kind: "link", label: "Tell us you're interested", href: PLANNED_PLANS_HREF },
  },
  {
    id: "classroom",
    name: "Classroom",
    monthlyPrice: 100,
    status: "planned",
    description: "For mentors, bootcamps and teachers",
    features: [
      "Everything in Pro",
      "Up to 30 students",
      "Shared assignments and rubrics",
      "Class dashboard and CSV export",
      "Custom grade weights",
    ],
    cta: { kind: "link", label: "Tell us you're interested", href: PLANNED_PLANS_HREF },
  },
];
