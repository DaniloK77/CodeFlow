import { PageShell } from "@/components/layout/PageShell";
import { Features } from "@/components/sections/Features";
import { Grading } from "@/components/sections/Grading";
import { Hero } from "@/components/sections/hero/Hero";
import { Pricing } from "@/components/sections/Pricing";
import { Rules } from "@/components/sections/Rules";
import { useDocumentTitle } from "@/hooks/useDocumentTitle";

export const LANDING_TITLE = "CodeFlow: honest code review for students and junior developers";

export function LandingPage() {
  useDocumentTitle(LANDING_TITLE);
  return (
    <PageShell>
      <Hero />
      <Features />
      <Grading />
      <Rules />
      <Pricing />
    </PageShell>
  );
}
