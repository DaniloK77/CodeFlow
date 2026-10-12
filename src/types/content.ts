import type { ComponentType, SVGAttributes } from "react";

export interface NavLink {
  label: string;
  href: string;
}

export type IconComponent = ComponentType<SVGAttributes<SVGSVGElement>>;

export interface SocialLink extends NavLink {
  icon: IconComponent;
}

export interface FooterLinkGroup {
  title: string;
  links: readonly NavLink[];
}

export type CodeLanguage = "jsx" | "tsx" | "javascript" | "typescript" | "python" | "bash";

export interface CodeSnippet {
  language: CodeLanguage;
  code: string;
}

/** Languages the analysis API accepts for pasted code. */
export type SourceLanguage = "typescript" | "tsx" | "javascript" | "jsx" | "python";

export type GradeName = "Excellent" | "Good" | "Poor";

/** A finding of the static analysis, as recorded for an example (see exampleReports.generated.json). */
export interface ExampleFinding {
  rule: string;
  severity: "error" | "warning" | "info";
  line: number;
  message: string;
}

/** What the real engine reported for an example, without any AI review. */
export interface ExampleReport {
  quality: number;
  codeLines: number;
  findings: readonly ExampleFinding[];
  checks: readonly { source: string; name: string; status: string; detail: string }[];
}

/**
 * A complete sample submission: the task, a solution and the author's explanation. The hero
 * shows them side by side; the analyzer offers them as one-click examples.
 */
export interface AssignmentExample {
  id: string;
  label: string;
  task: string;
  explanation: string;
  fileName: string;
  language: SourceLanguage;
  code: string;
}

export interface Feature {
  id: string;
  title: string;
  description: string;
  snippet: CodeSnippet;
  /** Label for a button that opens the free code analyzer. */
  tryItLabel?: string;
}

export type PlanCallToAction =
  { kind: "analyzer"; label: string } | { kind: "link"; label: string; href: string };

/** `planned` plans are on the roadmap but not built; the page says so instead of selling them. */
export type PlanStatus = "available" | "planned";

export interface PricingPlan {
  id: string;
  name: string;
  description: string;
  /** Monthly price in euros. */
  monthlyPrice: number;
  features: readonly string[];
  cta: PlanCallToAction;
  status: PlanStatus;
}
