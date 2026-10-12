"""Static checks: names from the task and explanation, looked up in the code."""

from __future__ import annotations

from tools.codegrade.assignment import Assignment, StaticCheck
from tools.codegrade.task_signals import Mention, mentions, static_checks

from .helpers import make_source

PAIR_SUMS = """
    def pair_sums(numbers, target):
        seen = set()
        return [(n, target - n) for n in numbers if target - n in seen or seen.add(n)]
"""


def checks_for(
    task: str, explanation: str, code: str, name: str
) -> dict[tuple[str, str], StaticCheck]:
    found = static_checks(Assignment(task, explanation), [make_source(code, name)])
    return {(check.source, check.name): check for check in found}


def test_finds_names_written_as_code_calls_or_introductions() -> None:
    text = (
        "Write a function called pairSums. `pair_sums(numbers, target)` uses seenValues; "
        "call add(1, 2)."
    )
    assert mentions(text, introduced=True) == [
        Mention("pairSums"),
        Mention("pair_sums", 2),
        Mention("seenValues"),
        Mention("add", 2),
    ]


def test_prose_literals_and_plurals_are_not_names() -> None:
    text = "Return `null` or `true` for the item(s). JavaScript is fine. Use `/api/users`."
    assert mentions(text, introduced=True) == []


def test_nested_arguments_are_counted_at_the_top_level() -> None:
    assert mentions("pairSums([1, 2, 3], 4)", introduced=False) == [Mention("pairSums", 2)]
    assert mentions("`render(...)`", introduced=False) == [Mention("render")]


def test_a_function_the_task_names_is_found_with_its_location() -> None:
    checks = checks_for("Write `pair_sums(numbers, target)`.", "", PAIR_SUMS, "solution.py")
    check = checks[("task", "pair_sums")]
    assert check.status == "found"
    assert check.detail == "defined at solution.py:1"


def test_a_missing_function_is_reported() -> None:
    checks = checks_for("Write a function called merge_intervals.", "", PAIR_SUMS, "solution.py")
    assert checks[("task", "merge_intervals")].status == "missing"


def test_a_differently_spelled_name_is_a_mismatch() -> None:
    checks = checks_for("Write `pairSums(numbers, target)`.", "", PAIR_SUMS, "solution.py")
    check = checks[("task", "pairSums")]
    assert check.status == "mismatch"
    assert "`pair_sums`" in check.detail


def test_a_wrong_parameter_count_is_a_mismatch() -> None:
    checks = checks_for("Write `pair_sums(numbers)`.", "", PAIR_SUMS, "solution.py")
    check = checks[("task", "pair_sums")]
    assert check.status == "mismatch"
    assert "2 parameter(s)" in check.detail


def test_optional_and_rest_parameters_widen_what_fits() -> None:
    code = """
        export function format(value: number, digits = 2, ...rest: string[]): string {
          return [value.toFixed(digits), ...rest].join(" ");
        }
    """
    assert checks_for("Use `format(1)`.", "", code, "a.ts")[("task", "format")].status == "found"
    assert (
        checks_for("Use `format(1, 2, 3, 4)`.", "", code, "a.ts")[("task", "format")].status
        == "found"
    )
    assert checks_for("Use `format()`.", "", code, "a.ts")[("task", "format")].status == "mismatch"


def test_components_hooks_and_used_apis_are_found_in_javascript() -> None:
    code = """
        export const TodoList = ({ items }) => {
          const [filter, setFilter] = useState("");
          return <ul>{items.map((item) => <li key={item.id}>{item.title}</li>)}</ul>;
        };
    """
    checks = checks_for("Build a component called TodoList with `useState`.", "", code, "Todo.jsx")
    assert checks[("task", "TodoList")].detail == "defined at Todo.jsx:1"
    assert checks[("task", "useState")].detail == "used in the code"


def test_an_explanation_that_describes_other_code_is_caught() -> None:
    explanation = (
        "I keep a `cache` dictionary and call sortPairs() at the end; `seen` tracks numbers."
    )
    checks = checks_for("", explanation, PAIR_SUMS, "solution.py")
    assert checks[("explanation", "cache")].status == "missing"
    assert checks[("explanation", "sortPairs")].status == "missing"
    assert checks[("explanation", "seen")].status == "found"


def test_no_names_means_no_checks() -> None:
    assert (
        static_checks(
            Assignment("Sort the list.", "I sorted it."), [make_source(PAIR_SUMS, "a.py")]
        )
        == ()
    )


def test_code_with_a_syntax_error_is_still_searched() -> None:
    checks = checks_for(
        "", "`pair_sums` loops once.", "def pair_sums(numbers, target:\n    pass\n", "a.py"
    )
    assert checks[("explanation", "pair_sums")].status == "found"
