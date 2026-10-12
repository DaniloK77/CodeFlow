import unittest

from tools.codegrade.models import Severity
from tools.codegrade.py_analyzer import analyze_python

from .helpers import make_source


def findings_for(code: str, name: str = "module.py") -> dict[str, str]:
    """rule → message for one module (each style rule fires at most once per file)."""
    structure = analyze_python(make_source(code, name))
    return {finding.rule: finding.message for finding in structure.findings}


class NamingTest(unittest.TestCase):
    def test_lists_single_letter_names(self) -> None:
        found = findings_for(
            """
            def f(l):
                r = [x for x in l]
                for i in range(3):
                    r.append(i)
                return r
            """
        )

        self.assertIn("`f`, `l`, `r`", found["short-names"])
        self.assertNotIn("`x`", found["short-names"])  # comprehension variable
        self.assertNotIn("`i`", found["short-names"])  # conventional loop index

    def test_descriptive_names_are_clean(self) -> None:
        found = findings_for("def total(prices: list[float]) -> float:\n    return sum(prices)\n")
        self.assertNotIn("short-names", found)


class MagicNumberTest(unittest.TestCase):
    def test_flags_unexplained_numbers_in_function_bodies(self) -> None:
        found = findings_for(
            """
            TAX_RATE = 0.21

            def price(net, discount=0.15):
                return net * 1.21 - 3 + 7 * 0
            """
        )

        self.assertIn("1.21, 3, 7", found["magic-numbers"])  # constants and defaults are named

    def test_a_few_numbers_are_a_note_and_a_habit_is_a_warning(self) -> None:
        few = analyze_python(make_source("def scale(value):\n    return value * 3 + 4\n", "m.py"))
        many = analyze_python(
            make_source("def scale(value):\n    return value * 3 + 4 - 5 / 6 * 7\n", "m.py")
        )
        severity = lambda structure: next(  # noqa: E731
            f.severity for f in structure.findings if f.rule == "magic-numbers"
        )
        self.assertIs(severity(few), Severity.INFO)
        self.assertIs(severity(many), Severity.WARNING)


class LoopTest(unittest.TestCase):
    def test_flags_pairwise_loops_and_range_len(self) -> None:
        found = findings_for(
            """
            def pairs(items, other):
                for i in range(len(items)):
                    for j in range(len(items)):
                        pass
                for item in items:
                    for value in other:
                        pass
            """
        )

        self.assertIn("same collection", found["nested-loops"])
        self.assertIn("enumerate", found["range-len"])

    def test_nested_loops_over_different_collections_are_fine(self) -> None:
        found = findings_for(
            "def grid(rows, cols):\n    for r in rows:\n        for c in cols:\n            pass\n"
        )
        self.assertNotIn("nested-loops", found)


class DocumentationTest(unittest.TestCase):
    def test_reports_missing_docstrings_and_type_hints(self) -> None:
        found = findings_for(
            """
            def load(path):
                text = open(path).read()
                lines = text.splitlines()
                cleaned = [line.strip() for line in lines]
                return cleaned

            def _helper(value):
                return value
            """
        )

        self.assertIn("`load`", found["missing-docstrings"])
        self.assertIn("`load`", found["missing-type-hints"])
        self.assertNotIn("_helper", found["missing-type-hints"])  # private helpers are exempt

    def test_documented_typed_code_is_clean(self) -> None:
        found = findings_for(
            '''
            def load(path: str) -> list[str]:
                """Non-empty lines of a text file."""
                with open(path) as handle:
                    lines = handle.read().splitlines()
                return [line for line in lines if line]
            '''
        )

        self.assertNotIn("missing-docstrings", found)
        self.assertNotIn("missing-type-hints", found)


class SideEffectTest(unittest.TestCase):
    def test_flags_code_that_runs_on_import(self) -> None:
        found = findings_for('print("hi")\n\nif __name__ == "__main__":\n    print("ok")\n')
        self.assertIn("1 statement(s) run on import", found["import-side-effects"])

    def test_test_files_skip_style_rules(self) -> None:
        found = findings_for("def f(l):\n    print(l * 37 + 41 - 43)\n", "test_module.py")
        self.assertEqual(found, {})


class NestingTest(unittest.TestCase):
    def test_elif_chains_count_once(self) -> None:
        structure = analyze_python(
            make_source(
                """
                def label(score: int) -> str:
                    if score > 90:
                        return "a"
                    elif score > 70:
                        return "b"
                    elif score > 50:
                        return "c"
                    return "d"
                """,
                "labels.py",
            )
        )

        self.assertEqual(structure.functions[0].max_nesting, 1)
