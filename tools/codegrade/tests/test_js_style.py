"""Readability, typing and documentation rules for JavaScript and TypeScript."""

from __future__ import annotations

import pytest

from .helpers import analyze, rules_in

LONG_BODY = "\n".join(f"  steps.push(compute(input, {{ step: STEPS[{n}] }}));" for n in range(14))
UNDOCUMENTED = f"export function build(input: Input): Step[] {{\n{LONG_BODY}\n  return steps;\n}}"
DOCUMENTED = f"/** Builds every step for the input. */\n{UNDOCUMENTED}"

CASES = [
    (
        "short-names",
        "const d = compute();\nshow(d);",
        "const distance = compute();\nshow(distance);",
    ),
    (
        "naming-convention",
        "const user_name = read();\nshow(user_name);",
        "const userName = read();\nshow(userName);",
    ),
    (
        "magic-numbers",
        "function price(amount: number): number { return amount * 37; }",
        "const RATE = 37;\nfunction price(amount: number): number { return amount * RATE; }",
    ),
    (
        "nested-ternary",
        "const label = first ? 'a' : second ? 'b' : 'c';",
        "const label = first ? 'a' : 'b';",
    ),
    ("no-console", "console.log(value);", "logger.report(value);"),
    (
        "commented-out-code",
        "// const total = items.length;\n// return total * price;\nrun();",
        "// Totals are computed on the server,\n// so nothing is summed here.\nrun();",
    ),
    (
        "untyped-params",
        "export function add(first, second) { return first + second; }",
        "export function add(first: number, second: number): number { return first + second; }",
    ),
    ("missing-docs", UNDOCUMENTED, DOCUMENTED),
]


@pytest.mark.parametrize(("rule", "bad", "good"), CASES)
def test_rule_fires_on_the_problem_and_not_on_the_fix(rule: str, bad: str, good: str) -> None:
    assert rule in rules_in(bad, "sample.ts")
    assert rule not in rules_in(good, "sample.ts")


def test_plain_javascript_without_any_types_is_flagged_once() -> None:
    code = """
        function add(first, second) { return first + second; }
        function subtract(first, second) { return first - second; }
    """
    assert rules_in(code, "math.js").count("no-types") == 1


def test_jsdoc_types_count_as_type_information() -> None:
    code = """
        /**
         * @param {number} first
         * @param {number} second
         * @returns {number}
         */
        function add(first, second) { return first + second; }
    """
    assert "no-types" not in rules_in(code, "math.js")


def test_callback_parameters_get_their_types_from_the_callee() -> None:
    code = "export const names = (users: User[]): string[] => users.map((user) => user.name);"
    assert "untyped-params" not in rules_in(code, "names.ts")


def test_loop_counters_and_coordinates_may_be_short() -> None:
    code = "for (let i = 0; i < size; i += 1) { draw(i); }"
    assert "short-names" not in rules_in(code, "draw.ts")


def test_numbers_with_a_name_next_to_them_are_not_magic() -> None:
    code = """
        const TIMEOUT_MS = 5000;
        function box(): Box { return { width: 320, height: 240 }; }
        function view(): Element { return <Icon size={24} />; }
    """
    assert "magic-numbers" not in rules_in(code)


def test_literal_values_in_tests_are_not_magic() -> None:
    code = "it('adds', () => { expect(add(7, 35)).toBe(42); });"
    assert "magic-numbers" not in rules_in(code, "inline.ts")


def test_console_calls_are_reported_together() -> None:
    findings = analyze("console.log(first);\nconsole.debug(second);", "log.ts").findings
    console = [finding for finding in findings if finding.rule == "no-console"]
    assert len(console) == 1
    assert "2 console" in console[0].message


def test_error_reporting_through_the_console_is_allowed() -> None:
    assert "no-console" not in rules_in("console.error(error);", "log.ts")


def test_style_rules_do_not_judge_test_files() -> None:
    code = "const d = 37 * 41;\nconsole.log(d);"
    assert rules_in(code, "price.test.ts") == []


def test_functions_in_a_typed_object_get_their_parameter_types_from_it() -> None:
    typed = """
        const handlers: Record<string, (message: string) => string> = {
          greet: (message) => message,
        };
    """
    untyped = "const handlers = { greet: (message) => message };"

    assert "untyped-params" not in rules_in(typed, "handlers.ts")
    assert "untyped-params" in rules_in(untyped, "handlers.ts")


def test_callbacks_passed_as_props_get_their_parameter_types_from_the_component() -> None:
    code = "const view = <Field onChange={(value) => save(value)} />;"

    assert "untyped-params" not in rules_in(code, "view.tsx")
