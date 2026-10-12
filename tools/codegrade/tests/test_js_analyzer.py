import time
import unittest

from .helpers import analyze


def functions_by_name(code: str, name: str = "sample.tsx"):
    structure = analyze(code, name)
    return {function.name: function for function in structure.functions}


class FunctionDetectionTest(unittest.TestCase):
    def test_finds_declarations_arrows_and_methods(self) -> None:
        functions = functions_by_name(
            """
            export function Card() {
              return <div />;
            }
            const useThing = () => {
              return 1;
            };
            class Store {
              load(id) {
                return id;
              }
            }
            """
        )

        self.assertTrue({"Card", "useThing", "load"} <= set(functions))
        self.assertEqual(functions["Card"].length, 3)
        self.assertEqual(functions["useThing"].length, 3)

    def test_arrow_with_parenthesised_jsx_body_spans_all_lines(self) -> None:
        functions = functions_by_name(
            """
            const Row = ({ item }) => (
              <li>
                {item.name}
              </li>
            );
            """
        )

        self.assertEqual(functions["Row"].length, 5)

    def test_ignores_overload_signatures_and_control_flow(self) -> None:
        functions = functions_by_name(
            """
            function parse(input: string): number;
            function parse(input: unknown) {
              if (input) {
                return 1;
              }
              return 0;
            }
            """,
            "sample.ts",
        )

        self.assertEqual(list(functions), ["parse"])
        self.assertEqual(functions["parse"].length, 6)


class ComplexityTest(unittest.TestCase):
    def test_counts_branches_loops_and_logical_operators(self) -> None:
        functions = functions_by_name(
            """
            function decide(a, b) {
              if (a && b) return 1;
              for (const x of a) {}
              return a ? b ?? 0 : 2;
            }
            """
        )

        # 1 + if + && + for + ternary + ??
        self.assertEqual(functions["decide"].complexity, 6)

    def test_ignores_optional_chaining_props_and_jsx_question_marks(self) -> None:
        functions = functions_by_name(
            """
            function View({ user }: { user?: User }) {
              return <p>Need help? {user?.name}</p>;
            }
            """
        )

        self.assertEqual(functions["View"].complexity, 1)

    def test_credits_decisions_to_the_innermost_function(self) -> None:
        functions = functions_by_name(
            """
            function List({ items }) {
              const handle = (item) => {
                if (item.done) return;
                if (item.hidden) return;
              };
              return items.length > 0 && <ul />;
            }
            """
        )

        self.assertEqual(functions["handle"].complexity, 3)
        self.assertEqual(functions["List"].complexity, 2)


class NestingTest(unittest.TestCase):
    def test_counts_control_blocks_not_jsx_markup(self) -> None:
        functions = functions_by_name(
            """
            function Page({ rows }) {
              for (const row of rows) {
                if (row.visible) {
                  while (row.pending) {
                    row.pending = false;
                  }
                }
              }
              return (
                <main>
                  <section>
                    <div>
                      <p>{rows.length}</p>
                    </div>
                  </section>
                </main>
              );
            }
            """
        )

        self.assertEqual(functions["Page"].max_nesting, 3)

    def test_else_if_chains_stay_flat(self) -> None:
        functions = functions_by_name(
            """
            function label(score) {
              if (score > 90) {
                return "a";
              } else if (score > 70) {
                return "b";
              } else {
                return "c";
              }
            }
            """
        )

        self.assertEqual(functions["label"].max_nesting, 1)

    def test_counts_parameters(self) -> None:
        functions = functions_by_name(
            """
            function create(name, { size, color }, ...rest) {}
            const add = (a, b) => a + b;
            """
        )

        self.assertEqual(functions["create"].params, 3)
        self.assertEqual(functions["add"].params, 2)

    def test_reports_nested_loops_over_the_same_collection_only(self) -> None:
        structure = analyze(
            """
            export function pairs(items, other) {
              for (const a of items) {
                for (const b of items) {}
                for (const c of other) {}
              }
              for (let i = 0; i < items.length; i++) {
                for (let j = 0; j < items.length; j++) {}
              }
            }
            """,
            "pairs.ts",
        )

        nested = [finding.line for finding in structure.findings if finding.rule == "nested-loops"]
        self.assertEqual(nested, [3, 7])


HOSTILE_PAYLOADS = {
    "unclosed arrow bodies": "x => {" * 50_000,
    "curried arrows": "const f = (a) => (b) => a && b;\n" * 9_000,
    "one huge line": "a(b => c ? d : e, " * 15_000,
    "bodiless functions": "function f()\n" * 25_000,
    "unclosed jsx tags": "<button " * 35_000,
    "deeply nested arrays": "[" * 40_000 + "7," * 40_000,
    "deeply nested calls": "f(" * 40_000,
    "deeply nested blocks": "if (a) { const b = 7;" * 20_000,
    "deeply nested jsx": "<div onClick={a}>" * 20_000,
    "nested ternaries": "a ? b : " * 30_000,
}


class AdversarialInputTest(unittest.TestCase):
    """Uploaded code is untrusted: analysis must stay roughly linear on hostile input."""

    BUDGET_SECONDS = 3.0  # the parser's own worst case is covered in test_isolation

    def test_hostile_payloads_finish_within_budget(self) -> None:
        for name, payload in HOSTILE_PAYLOADS.items():
            with self.subTest(payload=name):
                started = time.perf_counter()
                analyze(payload)
                self.assertLess(time.perf_counter() - started, self.BUDGET_SECONDS)
