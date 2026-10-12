import { DIMENSIONS, type Dimension } from "./dimensions";

export interface RuleDoc {
  title: string;
  why: string;
  dimension: Dimension;
}

/**
 * Plain-language explanations shown next to each finding and in the rule catalog. Keys are
 * codegrade rule ids; `dimension` mirrors the engine (checked by test_web_contract.py).
 */
const RULE_DOCS: Readonly<Record<string, RuleDoc>> = {
  "syntax-error": {
    title: "Syntax error",
    why: "The file doesn't parse, so it can't run, and nothing else in it can be trusted. A file with syntax errors can't score above 40.",
    dimension: "reliability",
  },
  "no-eval": {
    title: "eval / exec",
    why: "Runs a string as code: a security hole no tool can analyse. Use a parser, a lookup table or a function instead.",
    dimension: "reliability",
  },
  "no-debugger": {
    title: "debugger statement",
    why: "Freezes the page for anyone with DevTools open. Never ship it.",
    dimension: "reliability",
  },
  "sql-injection": {
    title: "SQL built from strings",
    why: "Gluing user input into a query lets an attacker rewrite it. Pass values as query parameters.",
    dimension: "reliability",
  },
  "shell-injection": {
    title: "Shell command from a string",
    why: "`shell=True` with built strings lets input run arbitrary commands. Pass an argument list instead.",
    dimension: "reliability",
  },
  "hardcoded-secret": {
    title: "Hardcoded secret",
    why: "Anything committed to a repository is public to everyone who can read it, forever. Load keys from the environment.",
    dimension: "reliability",
  },
  "dangerous-html": {
    title: "Raw HTML injection",
    why: "innerHTML and dangerouslySetInnerHTML bypass escaping and invite XSS. Render text, or sanitise the HTML first.",
    dimension: "reliability",
  },
  eqeqeq: {
    title: "Loose equality",
    why: '== converts types first, so "0" == 0 is true. === compares exactly.',
    dimension: "reliability",
  },
  "no-var": {
    title: "var declaration",
    why: "var is function-scoped and hoisted, which causes subtle bugs. Use const, or let when it changes.",
    dimension: "reliability",
  },
  "empty-catch": {
    title: "Swallowed error",
    why: "An empty catch hides failures. Handle, report or rethrow the error.",
    dimension: "reliability",
  },
  "bare-except": {
    title: "Bare except",
    why: "Also catches KeyboardInterrupt and SystemExit. Catch the exceptions you can actually handle.",
    dimension: "reliability",
  },
  "swallowed-exception": {
    title: "Exception ignored",
    why: "`except …: pass` turns a failure into silence. Log it, handle it or let it propagate.",
    dimension: "reliability",
  },
  "broad-except": {
    title: "Overly broad except",
    why: "`except Exception` that neither logs nor re-raises hides unexpected bugs. Catch the errors you expect.",
    dimension: "reliability",
  },
  "mutable-default": {
    title: "Mutable default argument",
    why: "The default is created once and shared by every call, so state leaks between them.",
    dimension: "reliability",
  },
  "no-global": {
    title: "Global state",
    why: "Global mutation couples functions together and makes tests depend on run order.",
    dimension: "reliability",
  },
  "compare-to-none": {
    title: "Comparison to None with ==",
    why: "Use `is None`: == can be overridden by the object being compared.",
    dimension: "reliability",
  },
  "request-without-timeout": {
    title: "HTTP request without timeout",
    why: "Without a timeout one slow server can hang your program forever. Always pass `timeout=`.",
    dimension: "reliability",
  },
  "unchecked-response": {
    title: "Response status not checked",
    why: "fetch() and requests succeed on 404 and 500 too. Check `response.ok` or call `raise_for_status()` before using the body.",
    dimension: "reliability",
  },
  "unhandled-rejection": {
    title: "Promise without a catch",
    why: "A rejected promise nobody handles fails silently. Add `.catch()`, or use try/catch around await.",
    dimension: "reliability",
  },
  "unguarded-json-parse": {
    title: "JSON.parse outside try/catch",
    why: "Malformed input makes JSON.parse throw. Guard it where the data comes from outside.",
    dimension: "reliability",
  },
  "open-without-with": {
    title: "File opened without `with`",
    why: "If anything fails before close(), the file stays open. `with open(...)` closes it for you.",
    dimension: "reliability",
  },
  "unreachable-code": {
    title: "Unreachable code",
    why: "Statements after return, raise, break or continue never run. Delete them or fix the logic.",
    dimension: "reliability",
  },
  "unused-import": {
    title: "Unused import",
    why: "Dead imports slow reading and hint at code that was never finished.",
    dimension: "reliability",
  },
  "unused-variable": {
    title: "Unused variable",
    why: "A value that's computed and never read is usually a bug or leftover. Remove it, or prefix it with `_` if intentional.",
    dimension: "reliability",
  },
  "shadowed-builtin": {
    title: "Shadowed built-in",
    why: "Naming a variable `list` or `id` hides the built-in for the rest of the scope and causes confusing errors.",
    dimension: "reliability",
  },
  "import-side-effects": {
    title: "Code runs on import",
    why: 'Module-level statements run whenever the file is imported, tests included. Put them under `if __name__ == "__main__":`.',
    dimension: "reliability",
  },
  "listener-cleanup": {
    title: "Listener never removed",
    why: "Listeners that are added and never removed pile up and keep old objects alive.",
    dimension: "reliability",
  },
  "effect-cleanup": {
    title: "Effect without cleanup",
    why: "Listeners, timers and subscriptions started in useEffect must be stopped in its cleanup, or they leak on every re-render.",
    dimension: "reliability",
  },
  "effect-race": {
    title: "Fetch in effect without cancellation",
    why: "A slow response can arrive after the component changed or unmounted and overwrite newer data. Abort the request in the cleanup.",
    dimension: "reliability",
  },
  "state-mutation": {
    title: "State mutated in place",
    why: "React compares state by reference. push(), sort() or assigning a property won't re-render; copy first, then set.",
    dimension: "reliability",
  },
  "index-as-key": {
    title: "Index used as key",
    why: "When the list changes order, React reuses the wrong elements and their state.",
    dimension: "reliability",
  },
  "missing-key": {
    title: "List item without a key",
    why: "React needs a stable key per item to update lists correctly and without warnings.",
    dimension: "reliability",
  },
  "ts-suppression": {
    title: "Suppressed type error",
    why: "@ts-ignore hides this error and any future one on the same line. Fix the type, or use @ts-expect-error with a reason.",
    dimension: "reliability",
  },
  "non-null-assertion": {
    title: "Non-null assertion",
    why: "`value!` tells TypeScript to stop checking. If you're wrong it crashes at runtime; narrow the type instead.",
    dimension: "reliability",
  },
  "function-length": {
    title: "Long function",
    why: "Long functions do several jobs at once. Split them so each part can be named, read and tested on its own.",
    dimension: "complexity",
  },
  complexity: {
    title: "High complexity",
    why: "Every branch is another path to test. Past about ten, bugs hide in combinations nobody exercised.",
    dimension: "complexity",
  },
  "deep-nesting": {
    title: "Deep nesting",
    why: "Every nested if or loop multiplies the paths through the code. Return early or extract a function.",
    dimension: "complexity",
  },
  "file-length": {
    title: "Large file",
    why: "Big files mix responsibilities. Split by feature so changes stay local.",
    dimension: "complexity",
  },
  duplication: {
    title: "Duplicated code",
    why: "Fix a bug in one copy and it survives in the other. Extract the shared part.",
    dimension: "complexity",
  },
  "nested-loops": {
    title: "Nested loops over the same data",
    why: "Comparing every item with every other is O(n²): 1,000 items means a million steps. A set or map lookup usually does it in one pass.",
    dimension: "complexity",
  },
  "too-many-params": {
    title: "Too many parameters",
    why: "Long parameter lists are easy to call in the wrong order. Group related values into an object.",
    dimension: "complexity",
  },
  "short-names": {
    title: "Single-letter names",
    why: "Names like `a` or `r` make the reader work out what they hold. A descriptive name is documentation that can't go stale.",
    dimension: "readability",
  },
  "magic-numbers": {
    title: "Unexplained numbers",
    why: "A bare 7 or 1.2 hides its meaning and is easy to change in one place but not another. Give it a named constant.",
    dimension: "readability",
  },
  "naming-convention": {
    title: "Naming convention",
    why: "Each language has a style (camelCase in JavaScript, snake_case and CapWords in Python). Following it makes code readable to everyone.",
    dimension: "readability",
  },
  "nested-ternary": {
    title: "Nested ternary",
    why: "a ? b : c ? d : e has to be parsed in your head. Use if/else, or a lookup.",
    dimension: "readability",
  },
  "commented-out-code": {
    title: "Commented-out code",
    why: "Version control remembers old code. Dead code in comments only adds noise and doubt.",
    dimension: "readability",
  },
  "no-console": {
    title: "Console logging",
    why: "Leaks internals and noise into production consoles. Remove it, or use a real logger.",
    dimension: "readability",
  },
  "todo-comment": {
    title: "Open TODO",
    why: "Track unfinished work in an issue, where it can't be forgotten.",
    dimension: "readability",
  },
  "lint-suppression": {
    title: "Suppressed lint rule",
    why: "Fine when justified. Leave a comment saying why.",
    dimension: "readability",
  },
  "range-len": {
    title: "range(len(…)) loop",
    why: "Looping over the list directly, or with enumerate(), is shorter and avoids index mistakes.",
    dimension: "readability",
  },
  "wildcard-import": {
    title: "Wildcard import",
    why: "Hides where names come from and can silently shadow others.",
    dimension: "readability",
  },
  "compare-to-bool": {
    title: "Comparison to True/False",
    why: "`if flag == True` is just `if flag`. The comparison adds nothing and can mask truthiness bugs.",
    dimension: "readability",
  },
  "missing-docstrings": {
    title: "Missing docstrings",
    why: "A one-line docstring tells callers what a function does without making them read it.",
    dimension: "documentation",
  },
  "missing-type-hints": {
    title: "Missing type hints",
    why: "Type hints document inputs and outputs, and let tools such as mypy catch mistakes before you run the code.",
    dimension: "documentation",
  },
  "missing-docs": {
    title: "Missing doc comments",
    why: "Exported functions are an API. A short comment saying what they do and what they return saves every caller from reading the body.",
    dimension: "documentation",
  },
  "no-types": {
    title: "No type information",
    why: "Plain JavaScript gives callers no hint what to pass. Use TypeScript, or at least JSDoc @param types.",
    dimension: "documentation",
  },
  "untyped-params": {
    title: "Untyped parameters",
    why: "TypeScript without parameter types falls back to `any` and loses most of its value.",
    dimension: "documentation",
  },
  "no-explicit-any": {
    title: "Explicit any",
    why: "any switches the type checker off for everything it touches. Use unknown and narrow it.",
    dimension: "documentation",
  },
  "img-alt": {
    title: "Image without alt text",
    why: 'Screen readers read out the file name instead. Describe the image, or use alt="" if it\'s decorative.',
    dimension: "accessibility",
  },
  "button-type": {
    title: "Button without type",
    why: 'Buttons default to type="submit" and will submit any form around them.',
    dimension: "accessibility",
  },
  "placeholder-href": {
    title: "Dead link",
    why: 'href="#" jumps to the top of the page and confuses screen readers. Link somewhere real, or use a button.',
    dimension: "accessibility",
  },
  "click-non-interactive": {
    title: "Click on a non-interactive element",
    why: "A <div> or <li> with onClick can't be reached with Tab or triggered with Enter. Use a <button>.",
    dimension: "accessibility",
  },
  "input-label": {
    title: "Form field without a label",
    why: "Screen readers announce an unlabelled field as just “edit text”. Connect a <label>, or add aria-label.",
    dimension: "accessibility",
  },
  "no-tests": {
    title: "No tests",
    why: "Nothing shows the code works, or keeps working after the next change. Even a few tests of the main path and the edge cases count.",
    dimension: "testing",
  },
};

export function describeRule(
  rule: string,
): RuleDoc | { title: string; why: string; dimension: null } {
  return RULE_DOCS[rule] ?? { title: rule, why: "", dimension: null };
}

/** Every documented rule, grouped by the dimension it belongs to (in schema order). */
export function rulesByDimension(): Record<Dimension, readonly (RuleDoc & { id: string })[]> {
  const grouped = Object.fromEntries(
    DIMENSIONS.map((dimension) => [dimension, []]),
  ) as unknown as Record<Dimension, (RuleDoc & { id: string })[]>;
  for (const [id, doc] of Object.entries(RULE_DOCS)) grouped[doc.dimension].push({ id, ...doc });
  return grouped;
}
