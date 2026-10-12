"""Structure of a JavaScript/TypeScript file: functions, complexity, nesting, syntax errors."""

from __future__ import annotations

from tree_sitter import Node

from .js_parser import (
    FUNCTION_TYPES,
    TEST_CALLS,
    JsModule,
    ancestors,
    function_name,
    line,
    parameters,
    text,
    walk,
)
from .models import Finding, FunctionMetrics, Severity, Structure

_DECISIONS = frozenset(
    {
        "if_statement",
        "for_statement",
        "for_in_statement",
        "while_statement",
        "do_statement",
        "switch_case",
        "catch_clause",
        "ternary_expression",
    }
)
_LOGICAL_OPERATORS = frozenset({"&&", "||", "??"})
_BLOCKS = frozenset(
    {
        "if_statement",
        "for_statement",
        "for_in_statement",
        "while_statement",
        "do_statement",
        "switch_statement",
        "try_statement",
    }
)
_LOOPS = frozenset({"for_statement", "for_in_statement"})
MAX_SYNTAX_FINDINGS = 3
_SNIPPET_LENGTH = 24


def analyze_js(module: JsModule) -> Structure:
    """Function metrics and structural findings for one parsed JS/TS file."""
    functions = [_metrics(node) for node in module.nodes(*FUNCTION_TYPES)]
    functions.sort(key=lambda function: function.start_line)
    findings = [*syntax_findings(module), *_nested_loop_findings(module)]
    return Structure(
        functions=functions,
        findings=findings,
        max_nesting=max((function.max_nesting for function in functions), default=0),
        has_tests=next(module.calls(*TEST_CALLS), None) is not None,
    )


def _metrics(function: Node) -> FunctionMetrics:
    return FunctionMetrics(
        name=function_name(function),
        start_line=line(function),
        end_line=function.end_point[0] + 1,
        complexity=1 + sum(_is_decision(node) for node in _own_nodes(function)),
        max_nesting=_block_depth(function),
        params=len(parameters(function)),
    )


def _own_nodes(function: Node) -> list[Node]:
    """Nodes that belong to ``function`` itself, not to functions nested inside it."""
    own: list[Node] = []
    stack = list(function.children)
    while stack:
        node = stack.pop()
        own.append(node)
        if node.type not in FUNCTION_TYPES:
            stack.extend(node.children)
    return own


def _is_decision(node: Node) -> bool:
    if node.type in _DECISIONS:
        return True
    if node.type != "binary_expression":
        return False
    operator = node.child_by_field_name("operator")
    return operator is not None and operator.type in _LOGICAL_OPERATORS


def _block_depth(function: Node) -> int:
    """Deepest nesting of control blocks in a function; `else if` chains stay on one level."""
    deepest = 0
    stack: list[tuple[Node, int]] = [(child, 0) for child in function.children]
    while stack:
        node, depth = stack.pop()
        if node.type in FUNCTION_TYPES:
            continue
        if node.type in _BLOCKS and not _is_else_if(node):
            depth += 1
            deepest = max(deepest, depth)
        stack.extend((child, depth) for child in node.children)
    return deepest


def _is_else_if(node: Node) -> bool:
    return (
        node.type == "if_statement"
        and node.parent is not None
        and node.parent.type == "else_clause"
    )


def syntax_findings(module: JsModule) -> list[Finding]:
    """The first few places the parser gave up, one per line."""
    broken = [node for node in walk(module.root) if node.type == "ERROR" or node.is_missing]
    findings: list[Finding] = []
    seen_lines: set[int] = set()
    for node in sorted(broken, key=line):
        if line(node) in seen_lines:
            continue
        seen_lines.add(line(node))
        snippet = " ".join(text(node).split())[:_SNIPPET_LENGTH]
        what = f"missing `{node.type}`" if node.is_missing else f"unexpected `{snippet}`"
        findings.append(
            module.finding("syntax-error", Severity.ERROR, f"syntax error: {what}", node)
        )
        if len(findings) == MAX_SYNTAX_FINDINGS:
            break
    return findings


def _iterable(loop: Node) -> str:
    """What a loop walks over: `items` in `for (… of items)` and in `i < items.length`."""
    if loop.type == "for_in_statement":
        return text(loop.child_by_field_name("right"))
    condition = loop.child_by_field_name("condition")
    if condition is not None and condition.type == "expression_statement":
        condition = condition.named_children[0] if condition.named_children else None
    if condition is None or condition.type != "binary_expression":
        return ""
    return text(condition.child_by_field_name("right")).removesuffix(".length")


def _nested_loop_findings(module: JsModule) -> list[Finding]:
    """A loop over a collection inside a loop over the same collection: O(n²) pairs."""
    message = "nested loops over the same collection (O(n²)); a Set or Map lookup is often faster"
    findings = []
    for loop in module.nodes(*_LOOPS):
        target = _iterable(loop)
        outer = [parent for parent in ancestors(loop) if parent.type in _LOOPS]
        if target and any(_iterable(parent) == target for parent in outer):
            findings.append(module.finding("nested-loops", Severity.INFO, message, loop))
    return sorted(findings, key=lambda finding: finding.line)
