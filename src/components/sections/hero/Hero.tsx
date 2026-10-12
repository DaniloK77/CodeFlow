import { ArrowRight, Check, ListChecks, ScanSearch } from "lucide-react";

import { Spotlight } from "@/components/ui/Spotlight";
import { ASSIGNMENT_EXAMPLES } from "@/content/examples";
import { GradeLink } from "@/components/ui/GradeLink";
import { Link } from "@/lib/router";

import { CodePreview } from "./CodePreview";

export function Hero() {
  return (
    <section
      aria-labelledby="hero-title"
      className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 pt-20 pb-12 sm:px-6 sm:pt-24 lg:px-8"
    >
      <Backdrop />
      <div className="relative mx-auto grid w-full max-w-7xl grid-cols-1 items-center gap-10 text-center lg:grid-cols-2 lg:gap-12 lg:text-left">
        <div>
          <Headline />
          <CallsToAction />
          <TrustSignals />
        </div>
        <CodePreview samples={ASSIGNMENT_EXAMPLES} />
      </div>
    </section>
  );
}

function Backdrop() {
  return (
    <>
      <Spotlight />
      <div
        aria-hidden="true"
        className="absolute top-20 left-4 size-48 rounded-full bg-blue-500/10 blur-3xl motion-safe:animate-pulse sm:left-10 sm:size-72"
      />
      <div
        aria-hidden="true"
        className="absolute right-4 bottom-20 size-64 rounded-full bg-cyan-500/10 blur-3xl animation-delay-1000 motion-safe:animate-pulse sm:right-10 sm:size-96"
      />
    </>
  );
}

const LIGHT_GRADIENT =
  "block bg-linear-to-r from-white via-blue-100 to-cyan-100 bg-clip-text text-transparent";
const BRAND_GRADIENT =
  "block bg-linear-to-b from-blue-400 via-cyan-400 to-blue-400 bg-clip-text text-transparent";

function Headline() {
  return (
    <>
      <p className="mb-4 inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-3 py-2 text-xs text-blue-300 motion-safe:animate-fade-in-up sm:mb-6 sm:px-4 sm:text-sm">
        <ScanSearch aria-hidden="true" className="size-4 text-blue-400" />
        Free code review for students and junior developers
      </p>

      <h1
        id="hero-title"
        className="mb-4 text-4xl leading-tight font-semibold animation-delay-100 motion-safe:animate-fade-in-up sm:mb-6 sm:text-5xl"
      >
        <span className={LIGHT_GRADIENT}>Describe the Task.</span>
        <span className={BRAND_GRADIENT}>Submit Your Code.</span>
        <span className={LIGHT_GRADIENT}>Get an Honest Grade.</span>
      </h1>

      <p className="mx-auto mb-6 max-w-2xl text-base leading-relaxed text-gray-400 animation-delay-200 motion-safe:animate-fade-in-up sm:mb-8 lg:mx-0 lg:text-lg">
        Paste an assignment, your solution and how it works. CodeFlow scores the code strictly
        across 64 checks and looks up every function your task names. With an AI review it also
        verifies the task and grades it <span className="text-emerald-300">Excellent</span>,{" "}
        <span className="text-amber-300">Good</span> or <span className="text-rose-300">Poor</span>.
        Without one you get the score and an honest “task not verified”, never a made-up rank.
      </p>
    </>
  );
}

function CallsToAction() {
  return (
    <div className="mb-6 flex flex-col items-center justify-center gap-3 animation-delay-300 motion-safe:animate-fade-in-up sm:flex-row sm:gap-4 lg:justify-start">
      <GradeLink className="group flex w-full items-center justify-center gap-2 rounded-lg bg-linear-to-b from-blue-600 to-blue-400 px-6 py-3 text-sm font-semibold whitespace-nowrap transition-transform duration-300 hover:scale-102 sm:w-auto sm:px-6 sm:py-4 sm:text-base xl:px-8">
        Grade My Solution Free
        <ArrowRight
          aria-hidden="true"
          className="size-4 transition-transform duration-300 group-hover:translate-x-1 sm:size-5"
        />
      </GradeLink>
      <Link
        to="/#features"
        className="flex w-full items-center justify-center gap-2 rounded-lg border border-white/10 bg-white/5 px-6 py-3 text-sm font-semibold whitespace-nowrap backdrop-blur-sm transition-colors duration-300 hover:bg-white/10 sm:w-auto sm:px-6 sm:py-4 sm:text-base xl:px-8"
      >
        <ListChecks aria-hidden="true" className="size-4 sm:size-5" />
        See How It Works
      </Link>
    </div>
  );
}

const TRUST_SIGNALS = [
  "No sign-up",
  "History stays in your browser",
  "5 free AI reviews a day",
] as const;

function TrustSignals() {
  return (
    <ul className="flex flex-wrap items-center justify-center gap-x-5 gap-y-2 text-sm text-gray-400 animation-delay-300 motion-safe:animate-fade-in-up lg:justify-start">
      {TRUST_SIGNALS.map((signal) => (
        <li key={signal} className="flex items-center gap-1.5">
          <Check aria-hidden="true" className="size-4 text-emerald-400" />
          {signal}
        </li>
      ))}
    </ul>
  );
}
