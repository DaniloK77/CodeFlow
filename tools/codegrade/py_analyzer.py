"""Python analysis on the real AST: function metrics plus reliability and style findings."""

from __future__ import annotations

import ast
import io
import re
import tokenize

from .models import Finding, FunctionMetrics, Severity, Structure
from .py_rules import FunctionNode, reliability_findings
from .py_style import style_findings
from .source import SourceFile, is_test_file

_FUNCTION_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
_BRANCH_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.IfExp, ast.ExceptHandler)
_BLOCK_NODES = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.With, ast.AsyncWith, ast.Try)
_MATCH_CASE = getattr(ast, "match_case", None)
_MATCH = getattr(ast, "Match", None)
_TODO = re.compile(r"\b(?:TODO|FIXME|HACK|XXX)\b")
_COMMENTED_CODE = re.compile(
    r"^#\s*(def |class |import |from \w+ import |if .*:$|for .*:$|while .*:$|return\b|print\()"
)
MIN_COMMENTED_OUT_LINES = 2
_TEST_MODULES = frozenset({"pytest", "unittest"})


def analyze_python(source: SourceFile) -> Structure:
    """Function metrics and findings for one Python file (a syntax error is a finding)."""
    try:
        tree = ast.parse(source.raw)
    except SyntaxError as error:
        message = f"syntax error: {error.msg}"
        finding = Finding("syntax-error", Severity.ERROR, message, source.label, error.lineno or 1)
        return Structure(findings=[finding])
    except (RecursionError, MemoryError, ValueError):  # absurd nesting, or NUL bytes
        message = "syntax error: too deeply nested or malformed to parse"
        return Structure(
            findings=[Finding("syntax-error", Severity.ERROR, message, source.label, 1)]
        )

    functions = [_metrics(node) for node in ast.walk(tree) if isinstance(node, FunctionNode)]
    findings = [*reliability_findings(tree, source.label), *_comment_findings(source)]
    if not is_test_file(source.label):
        findings.extend(style_findings(tree, source.label))
    return Structure(
        functions=functions,
        findings=findings,
        max_nesting=max((function.max_nesting for function in functions), default=0),
        has_tests=_has_tests(tree),
    )


def _has_tests(tree: ast.Module) -> bool:
    """Whether the module carries its own tests: `test_*` functions or a test framework."""
    for node in ast.walk(tree):
        if isinstance(node, FunctionNode) and node.name.startswith("test_"):
            return True
        if isinstance(node, ast.Import) and any(a.name in _TEST_MODULES for a in node.names):
            return True
    return False


def _metrics(node: FunctionNode) -> FunctionMetrics:
    params = [*node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs]
    counted = [arg for arg in params if arg.arg not in {"self", "cls"}]
    return FunctionMetrics(
        name=node.name,
        start_line=node.lineno,
        end_line=node.end_lineno or node.lineno,
        complexity=_complexity(node),
        max_nesting=_block_depth(node.body),
        params=len(counted),
    )


def _complexity(function: ast.AST) -> int:
    """McCabe complexity of one function, excluding functions nested inside it."""
    score = 1
    pending = list(ast.iter_child_nodes(function))
    while pending:
        node = pending.pop()
        if isinstance(node, _FUNCTION_NODES):
            continue
        score += _decision_points(node)
        pending.extend(ast.iter_child_nodes(node))
    return score


def _decision_points(node: ast.AST) -> int:
    if isinstance(node, _BRANCH_NODES):
        return 1
    if isinstance(node, ast.BoolOp):
        return len(node.values) - 1
    if isinstance(node, ast.comprehension):
        return 1 + len(node.ifs)
    if _MATCH_CASE is not None and isinstance(node, _MATCH_CASE):
        return 1
    return 0


def _block_depth(statements: list[ast.stmt]) -> int:
    """Deepest nesting of control blocks (if/for/while/with/try) in a function body.

    ``elif`` chains count once, like the flat ladder they look like; nested functions are
    measured on their own.
    """
    deepest = 0
    for statement in statements:
        if isinstance(statement, (*_FUNCTION_NODES, ast.ClassDef)):
            continue
        if isinstance(statement, _BLOCK_NODES) or (_MATCH and isinstance(statement, _MATCH)):
            deepest = max(deepest, 1 + _inner_depth(statement))
    return deepest


def _inner_depth(block: ast.stmt) -> int:
    bodies: list[list[ast.stmt]] = [getattr(block, "body", [])]
    orelse = getattr(block, "orelse", [])
    if isinstance(block, ast.If) and len(orelse) == 1 and isinstance(orelse[0], ast.If):
        elif_depth = _inner_depth(orelse[0])  # elif: same level as the if
        return max(_block_depth(bodies[0]), elif_depth)
    bodies.append(orelse)
    bodies.append(getattr(block, "finalbody", []))
    bodies.extend(handler.body for handler in getattr(block, "handlers", []))
    bodies.extend(case.body for case in getattr(block, "cases", []))
    return max((_block_depth(body) for body in bodies), default=0)


def _comments(source: SourceFile) -> list[tuple[int, str]]:
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source.raw).readline))
    except (tokenize.TokenError, SyntaxError):
        return []
    return [(token.start[0], token.string) for token in tokens if token.type == tokenize.COMMENT]


def _comment_findings(source: SourceFile) -> list[Finding]:
    """Checks that must only look at real comments, never at string literals."""
    findings: list[Finding] = []
    dead_code: list[int] = []
    for line, comment in _comments(source):
        if _TODO.search(comment):
            message = "unresolved TODO / FIXME marker"
            findings.append(Finding("todo-comment", Severity.INFO, message, source.label, line))
        if "type: ignore" in comment or "noqa" in comment:
            message = "checker suppressed inline"
            findings.append(Finding("lint-suppression", Severity.INFO, message, source.label, line))
        if _COMMENTED_CODE.match(comment):
            dead_code.append(line)
    if len(dead_code) >= MIN_COMMENTED_OUT_LINES:
        message = f"{len(dead_code)} lines of commented-out code; delete them (git remembers)"
        findings.append(
            Finding("commented-out-code", Severity.INFO, message, source.label, dead_code[0])
        )
    return findings
