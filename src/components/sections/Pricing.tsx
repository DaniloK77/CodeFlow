import { Check } from "lucide-react";

import { Section } from "@/components/ui/Section";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { GradeLink } from "@/components/ui/GradeLink";
import { PLANNED_PLANS_HREF, PRICING_PLANS } from "@/content/pricing";
import { cn } from "@/lib/cn";
import { formatPrice } from "@/lib/format";
import type { PricingPlan } from "@/types/content";

export function Pricing() {
  return (
    <Section id="pricing" labelledBy="pricing-title">
      <SectionHeading
        id="pricing-title"
        title="Simple, Transparent"
        highlight="Pricing Plans"
        description="The free plan is complete and works today. Pro and Classroom are planned: nothing is for sale yet, and the buttons below only register your interest."
      />

      <ul className="mx-auto grid max-w-6xl grid-cols-1 gap-6 sm:gap-8 md:grid-cols-3 md:gap-6">
        {PRICING_PLANS.map((plan) => (
          <li key={plan.id} className="flex">
            <PricingCard plan={plan} />
          </li>
        ))}
      </ul>

      <p className="mt-8 text-center text-base text-gray-400 sm:mt-12 sm:text-lg">
        Teaching a class or running a bootcamp?{" "}
        <a
          href={PLANNED_PLANS_HREF}
          target="_blank"
          rel="noreferrer"
          className="text-blue-400 hover:text-blue-300"
        >
          Tell us what you'd need
        </a>
      </p>
    </Section>
  );
}

function PricingCard({ plan }: { plan: PricingPlan }) {
  const titleId = `plan-${plan.id}`;

  return (
    <article
      aria-labelledby={titleId}
      className={cn(
        "group relative flex w-full flex-col rounded-xl border bg-slate-900/50 p-6 backdrop-blur-sm transition-all duration-300 sm:rounded-2xl sm:p-8",
        plan.status === "available"
          ? "border-blue-500 shadow-2xl shadow-blue-500/20 lg:scale-105"
          : "border-slate-800 hover:border-slate-700",
      )}
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -translate-x-full -translate-y-full rounded-xl bg-linear-to-br from-white/10 via-transparent to-transparent opacity-0 transition-all duration-500 group-hover:translate-x-0 group-hover:translate-y-0 group-hover:opacity-100 sm:rounded-2xl"
      />
      {plan.status === "planned" ? <PlannedBadge /> : <AvailableBadge />}

      <div className="mb-6 text-center sm:mb-8">
        <h3 id={titleId} className="mb-2 text-xl font-bold sm:text-2xl">
          {plan.name}
        </h3>
        <p className="mb-3 text-xs text-gray-400 sm:mb-4 sm:text-sm">{plan.description}</p>
        <p className="flex items-baseline justify-center">
          <span className="bg-linear-to-r from-blue-400 to-cyan-400 bg-clip-text text-3xl font-bold text-transparent sm:text-4xl lg:text-5xl">
            {formatPrice(plan.monthlyPrice)}
          </span>
          <span className="ml-1 text-sm text-gray-400 sm:ml-2 sm:text-base">/month</span>
        </p>
      </div>

      <FeatureList planName={plan.name} features={plan.features} />

      <PlanButton plan={plan} />
    </article>
  );
}

function PlannedBadge() {
  return (
    <p className="absolute -top-3 left-1/2 z-10 -translate-x-1/2 rounded-full border border-white/20 bg-slate-800 px-3 py-1 text-xs font-semibold whitespace-nowrap">
      Planned · not available yet
    </p>
  );
}

function AvailableBadge() {
  return (
    <p className="absolute -top-3 left-1/2 z-10 -translate-x-1/2 rounded-full bg-linear-to-b from-blue-500 to-cyan-500 px-3 py-1 text-xs font-semibold whitespace-nowrap shadow-lg">
      Available now
    </p>
  );
}

function FeatureList({ planName, features }: { planName: string; features: readonly string[] }) {
  return (
    <ul aria-label={`${planName} features`} className="mb-6 space-y-3 sm:mb-8 sm:space-y-4">
      {features.map((feature) => (
        <li key={feature} className="flex items-start gap-2 sm:gap-3">
          <span
            aria-hidden="true"
            className="mt-0.5 flex size-4 shrink-0 items-center justify-center rounded-full bg-blue-500/20 sm:size-5"
          >
            <Check className="size-2.5 text-blue-400 sm:size-3" />
          </span>
          <span className="text-sm text-gray-300 sm:text-base">{feature}</span>
        </li>
      ))}
    </ul>
  );
}

const PLAN_BUTTON_CLASSES =
  "mt-auto block w-full rounded-lg px-4 py-2.5 text-center text-sm font-semibold transition-all duration-300 hover:scale-102 sm:px-6 sm:py-3 sm:text-base";

function PlanButton({ plan }: { plan: PricingPlan }) {
  const className = cn(
    PLAN_BUTTON_CLASSES,
    plan.cta.kind === "analyzer"
      ? "bg-linear-to-b from-blue-500 to-cyan-500"
      : "border border-white/10 bg-white/5 hover:bg-white/10",
  );
  const label = (
    <>
      {plan.cta.label} <span className="sr-only">({plan.name} plan)</span>
    </>
  );

  if (plan.cta.kind === "link") {
    return (
      <a href={plan.cta.href} target="_blank" rel="noreferrer" className={className}>
        {label}
      </a>
    );
  }
  return <GradeLink className={className}>{label}</GradeLink>;
}
