import { Section } from "@/components/ui/Section";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { DIMENSION_LABELS, DIMENSION_SUMMARIES, DIMENSIONS } from "@/features/analyzer/dimensions";
import { rulesByDimension } from "@/features/analyzer/ruleDocs";

const EXAMPLES_SHOWN = 4;

/** The rule catalog: what the static analysis actually looks for, straight from the engine's docs. */
export function Rules() {
  const grouped = rulesByDimension();
  const total = DIMENSIONS.reduce((sum, dimension) => sum + grouped[dimension].length, 0);

  return (
    <Section id="rules" labelledBy="rules-title" narrow>
      <SectionHeading
        id="rules-title"
        title={`${total} Checks Across`}
        highlight="Six Dimensions"
        description="Strict on purpose. Typical clean-looking code scores between 60 and 75, and 90 or more takes types, documentation, tests and small functions. Every rule is listed here."
      />
      <ul className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {DIMENSIONS.map((dimension) => (
          <li key={dimension}>
            <article className="flex h-full flex-col rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
              <h3 className="text-xl font-semibold">
                {DIMENSION_LABELS[dimension]}{" "}
                <span className="text-sm font-normal text-gray-500">
                  {grouped[dimension].length} rule{grouped[dimension].length === 1 ? "" : "s"}
                </span>
              </h3>
              <p className="mt-1 mb-4 text-sm text-gray-400">{DIMENSION_SUMMARIES[dimension]}</p>
              <ul className="mb-4 space-y-1.5 text-sm text-gray-300">
                {grouped[dimension].slice(0, EXAMPLES_SHOWN).map((rule) => (
                  <li key={rule.id}>{rule.title}</li>
                ))}
              </ul>
              {grouped[dimension].length > EXAMPLES_SHOWN && (
                <details className="mt-auto text-sm">
                  <summary className="cursor-pointer text-blue-300 hover:text-blue-200">
                    All {grouped[dimension].length} rules
                  </summary>
                  <ul className="mt-3 space-y-3">
                    {grouped[dimension].map((rule) => (
                      <li key={rule.id}>
                        <p className="font-medium text-gray-200">{rule.title}</p>
                        <p className="text-xs text-gray-400">{rule.why}</p>
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </article>
          </li>
        ))}
      </ul>
    </Section>
  );
}
