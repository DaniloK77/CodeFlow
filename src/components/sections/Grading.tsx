import { Section } from "@/components/ui/Section";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { GRADE_BANDS, GRADE_WEIGHTS, GRADING_PARTS, type GradingPart } from "@/content/grading";
import { cn } from "@/lib/cn";
import { GRADE_STYLES } from "@/lib/grades";

export function Grading() {
  return (
    <Section id="grading" labelledBy="grading-title" narrow>
      <SectionHeading
        id="grading-title"
        title="How Your Grade"
        highlight="Is Calculated"
        description="Three questions every good reviewer asks, each with its own score. Nothing is hidden: the report shows every point."
      />
      <ol className="grid gap-6 md:grid-cols-3">
        {GRADING_PARTS.map((part) => (
          <li key={part.id}>
            <GradingCard part={part} />
          </li>
        ))}
      </ol>
      <GradeBands />
    </Section>
  );
}

function GradingCard({ part }: { part: GradingPart }) {
  return (
    <article className="flex h-full flex-col rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
      <p className="mb-4 bg-linear-to-r from-blue-400 to-cyan-400 bg-clip-text text-5xl font-bold text-transparent">
        {GRADE_WEIGHTS[part.id]}%
      </p>
      <h3 className="mb-1 text-xl font-semibold">{part.title}</h3>
      <p className="mb-3 text-gray-300">{part.question}</p>
      <p className="mb-4 text-sm text-gray-400">{part.how}</p>
      <p className="mt-auto text-xs tracking-wide text-gray-500 uppercase">{part.gradedBy}</p>
    </article>
  );
}

function GradeBands() {
  return (
    <div className="mt-10 rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
      <ul className="grid gap-3 sm:grid-cols-3">
        {GRADE_BANDS.map((band) => (
          <li
            key={band.grade}
            className={cn("rounded-xl border px-4 py-3 text-center", GRADE_STYLES[band.grade].chip)}
          >
            <span className="block text-lg font-bold">{band.grade}</span>
            <span className="text-sm">
              {band.min}–{band.max}
            </span>
          </li>
        ))}
      </ul>
      <p className="mt-4 text-center text-sm text-gray-400">
        A rank needs the AI review. Without one you get the code-quality score and “task not
        verified”: code can be spotless and still solve the wrong problem.
      </p>
    </div>
  );
}
