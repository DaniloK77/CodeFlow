import time
import unittest

from tools.codegrade.py_analyzer import analyze_python

from .helpers import make_source, rules_of


def analyze(code: str):
    return analyze_python(make_source(code, "module.py"))


class PythonStructureTest(unittest.TestCase):
    def test_measures_function_length_and_complexity(self) -> None:
        structure = analyze(
            """
            def classify(values, strict=False):
                result = [v for v in values if v]
                for value in result:
                    if value > 10 and strict:
                        return "big"
                return "small"
            """
        )

        (function,) = structure.functions
        self.assertEqual(function.name, "classify")
        self.assertEqual(function.length, 6)
        # 1 + comprehension(for + if) + for + if + and
        self.assertEqual(function.complexity, 6)

    def test_nested_functions_are_measured_separately(self) -> None:
        structure = analyze(
            """
            def outer():
                def inner(x):
                    if x:
                        return 1
                return inner
            """
        )

        complexities = {function.name: function.complexity for function in structure.functions}
        self.assertEqual(complexities, {"outer": 1, "inner": 2})


class PythonRulesTest(unittest.TestCase):
    def test_flags_risky_constructs(self) -> None:
        structure = analyze(
            """
            from os import *

            def run(code, cache={}):
                global STATE
                try:
                    eval(code)
                except:
                    pass
            """
        )

        risky = {"bare-except", "mutable-default", "no-eval", "no-global", "wildcard-import"}
        self.assertTrue(risky <= set(rules_of(structure.findings)))

    def test_todo_inside_a_string_is_not_a_comment(self) -> None:
        structure = analyze(
            """
            MESSAGE = "TODO: this is data, not a reminder"
            # TODO: this one is real
            """
        )

        self.assertEqual(rules_of(structure.findings), ["todo-comment"])

    def test_syntax_errors_are_reported_not_raised(self) -> None:
        structure = analyze("def broken(:\n    pass\n")
        self.assertEqual(rules_of(structure.findings), ["syntax-error"])


class AdversarialPythonTest(unittest.TestCase):
    """The standard parser fails loudly on absurd nesting; the analyzer must not."""

    def test_pathological_sources_become_findings_not_crashes(self) -> None:
        payloads = {
            "nested brackets": "x = " + "[" * 5_000 + "]" * 5_000,
            "very long expression": "x = " + " + ".join(["1"] * 60_000),
            "null byte": "x = 1\x00\n",
            "deep calls": "f(" * 3_000 + ")" * 3_000,
        }
        for name, payload in payloads.items():
            with self.subTest(payload=name):
                started = time.perf_counter()
                structure = analyze(payload)
                self.assertLess(time.perf_counter() - started, 3.0)
                self.assertIsNotNone(structure)


class FalsePositiveTest(unittest.TestCase):
    """Things a linter must leave alone, or nobody trusts it."""

    def test_a_handler_that_logs_or_reports_is_not_hiding_the_error(self) -> None:
        code = """
            import logging
            logger = logging.getLogger(__name__)

            def run(job):
                try:
                    job()
                except Exception:
                    logger.exception("job failed")
        """
        self.assertNotIn("broad-except", rules_of(analyze(code).findings))

    def test_a_silent_broad_handler_is_still_flagged(self) -> None:
        code = """
            def run(job):
                try:
                    job()
                except Exception:
                    return None
        """
        self.assertIn("broad-except", rules_of(analyze(code).findings))

    def test_private_classes_and_a_parameter_named_file_are_fine(self) -> None:
        code = """
            class _Reader:
                def read(self, file: str) -> str:
                    return file
        """
        found = rules_of(analyze(code).findings)
        self.assertNotIn("naming-convention", found)
        self.assertNotIn("shadowed-builtin", found)
