import { CodeBlock } from "@/components/ui/CodeBlock";
import { Section } from "@/components/ui/Section";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { GradeLink } from "@/components/ui/GradeLink";
import { WindowControls } from "@/components/ui/WindowControls";
import { FEATURES } from "@/content/features";
import { cn } from "@/lib/cn";
import { ArrowRight } from "lucide-react";
import type { Feature } from "@/types/content";

const CODE_STYLE = {
  background: "transparent",
  padding: 0,
  fontSize: "0.75rem",
  lineHeight: "1.4",
} as const;

export function Features() {
  return (
    <Section id="features" labelledBy="features-title" narrow>
      <SectionHeading
        id="features-title"
        title="A Mentor's Review,"
        highlight="In About a Minute"
        description="Submit the task, your solution and your explanation. CodeFlow reviews all three the way a senior developer would, then turns what it finds into a grade and a list of next steps."
      />

      <div className="space-y-16 sm:space-y-20 lg:space-y-32">
        {FEATURES.map((feature, index) => (
          <FeatureRow key={feature.id} feature={feature} isReversed={index % 2 === 1} />
        ))}
      </div>
    </Section>
  );
}

function FeatureRow({ feature, isReversed }: { feature: Feature; isReversed: boolean }) {
  return (
    <article
      aria-labelledby={`feature-${feature.id}`}
      className={cn(
        "flex flex-col items-center gap-8 sm:gap-12 lg:flex-row",
        isReversed && "lg:flex-row-reverse",
      )}
    >
      <div className="group relative w-full flex-1">
        <div
          aria-hidden="true"
          className="absolute inset-0 rounded-xl bg-linear-to-br from-blue-500/20 to-purple-500/20 sm:rounded-2xl"
        />
        <div className="relative overflow-hidden rounded-xl border border-gray-700/50 bg-gray-900/50 p-4 backdrop-blur-sm transition-colors duration-300 group-hover:border-blue-600/50 sm:rounded-2xl sm:p-6">
          <div className="rounded-lg bg-gray-950 p-3 font-mono text-xs sm:p-4 sm:text-sm">
            <div aria-hidden="true" className="mb-3 flex items-center gap-2 sm:mb-4 sm:gap-4">
              <WindowControls />
              <span className="text-gray-400">{feature.title}</span>
            </div>
            <CodeBlock
              language={feature.snippet.language}
              code={feature.snippet.code}
              style={CODE_STYLE}
            />
          </div>
        </div>
      </div>

      <div className="w-full flex-1">
        <div className="mx-auto max-w-lg text-center lg:mx-0 lg:text-left">
          <h3
            id={`feature-${feature.id}`}
            className="mb-4 text-2xl font-bold text-white sm:mb-6 sm:text-3xl lg:text-4xl"
          >
            {feature.title}
          </h3>
          <p className="text-base leading-relaxed text-gray-300 sm:text-lg">
            {feature.description}
          </p>
          {feature.tryItLabel && <TryItButton label={feature.tryItLabel} />}
        </div>
      </div>
    </article>
  );
}

function TryItButton({ label }: { label: string }) {
  return (
    <GradeLink className="group mt-6 inline-flex items-center gap-2 rounded-lg border border-blue-400/30 bg-blue-500/10 px-5 py-2.5 text-sm font-semibold text-blue-100 transition-colors hover:bg-blue-500/20">
      {label}
      <ArrowRight
        aria-hidden="true"
        className="size-4 transition-transform group-hover:translate-x-1"
      />
    </GradeLink>
  );
}
