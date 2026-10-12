"""Reliability rules for JavaScript and TypeScript: each fires on bad code and not on its fix."""

from __future__ import annotations

import pytest

from .helpers import analyze, rules_in

# (rule, code that breaks it, the same code fixed)
CASES = [
    ("no-debugger", "debugger;", "const ready = true;"),
    ("no-eval", "eval(input);", "evaluate(input);"),
    ("no-eval", 'const run = new Function("return 1");', "const run = () => 1;"),
    ("no-var", "var total = 0;", "let total = 0;"),
    ("eqeqeq", "if (left == right) { run(); }", "if (left === right) { run(); }"),
    ("eqeqeq", "if (left != right) { run(); }", "if (left == null) { run(); }"),
    (
        "empty-catch",
        "try { run(); } catch (error) {}",
        "try { run(); } catch (error) { report(error); }",
    ),
    (
        "hardcoded-secret",
        'const apiKey = "sk_live_9f8a7b6c5d4e3f2a1b";',
        "const apiKey = process.env.API_KEY;",
    ),
    ("dangerous-html", "element.innerHTML = html;", "element.textContent = text;"),
    (
        "dangerous-html",
        "const view = <div dangerouslySetInnerHTML={{ __html: html }} />;",
        "const view = <div>{text}</div>;",
    ),
    ("ts-suppression", "// @ts-ignore\nrun();", "// runs the job\nrun();"),
    ("lint-suppression", "// eslint-disable-next-line no-console\nrun();", "run();"),
    ("todo-comment", "// TODO: handle errors\nrun();", "// handles errors\nrun();"),
    (
        "unreachable-code",
        "function stop() { return 1; cleanup(); }",
        "function stop() { cleanup(); return 1; }",
    ),
    (
        "unchecked-response",
        "async function load() { const response = await fetch(url); return response.json(); }",
        """
        async function load() {
          const response = await fetch(url);
          if (!response.ok) throw new Error("request failed");
          return response.json();
        }
        """,
    ),
    ("unhandled-rejection", "load().then(render);", "load().then(render).catch(report);"),
    (
        "unguarded-json-parse",
        "const data = JSON.parse(raw);",
        "try { store(JSON.parse(raw)); } catch (error) { report(error); }",
    ),
    (
        "listener-cleanup",
        'window.addEventListener("resize", onResize);',
        """
        window.addEventListener("resize", onResize);
        window.removeEventListener("resize", onResize);
        """,
    ),
    (
        "no-explicit-any",
        "export function show(value: any): void { render(value); }",
        "export function show(value: unknown): void { render(value); }",
    ),
    ("non-null-assertion", "const name = user!.name;", "const name = user?.name;"),
    (
        "unused-import",
        'import { useMemo, useState } from "react";\nuseState(0);',
        'import { useState } from "react";\nuseState(0);',
    ),
    (
        "unused-variable",
        "function total() { const unused = 1; return 2; }",
        "function total() { const used = 1; return used; }",
    ),
]


@pytest.mark.parametrize(("rule", "bad", "good"), CASES)
def test_rule_fires_on_the_problem_and_not_on_the_fix(rule: str, bad: str, good: str) -> None:
    assert rule in rules_in(bad)
    assert rule not in rules_in(good)


def test_every_violation_is_reported_on_its_own_line() -> None:
    code = """
        var first = 1;
        let second = 2;
        var third = 3;
    """
    lines = [finding.line for finding in analyze(code).findings if finding.rule == "no-var"]
    assert lines == [1, 3]


def test_code_inside_strings_and_comments_is_not_code() -> None:
    code = """
        // var legacy = eval("1"); debugger;
        export const hint: string = "use var or eval() or debugger; here";
    """
    assert rules_in(code, "hint.ts") == []


def test_exports_and_react_are_not_unused() -> None:
    code = """
        import React from "react";
        export const LIMIT = 5;
        export function Title(): React.ReactNode { return <h1>Title</h1>; }
    """
    assert "unused-variable" not in rules_in(code)
    assert "unused-import" not in rules_in(code)


def test_a_response_checked_by_status_counts_as_checked() -> None:
    code = """
        async function load(url: string): Promise<unknown> {
          const response = await fetch(url);
          if (response.status !== 200) return null;
          return response.json();
        }
    """
    assert "unchecked-response" not in rules_in(code)


def test_awaited_promises_inside_try_are_handled() -> None:
    code = """
        async function run(): Promise<void> {
          try { await load().then(render); } catch (error) { report(error); }
        }
    """
    assert "unhandled-rejection" not in rules_in(code)


def test_a_two_argument_then_handles_rejection() -> None:
    assert "unhandled-rejection" not in rules_in("load().then(render, report);")


def test_a_response_handed_back_to_the_caller_is_checked_there() -> None:
    code = """
        async function send(path: string): Promise<Response> {
          return await fetch(path);
        }
        const get = (path: string) => fetch(path);
    """
    assert "unchecked-response" not in rules_in(code)
