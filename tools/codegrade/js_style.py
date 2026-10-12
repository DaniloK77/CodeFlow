"""Readability, documentation and typing rules for JavaScript/TypeScript."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator

from tree_sitter import Node

from .js_parser import (
    FUNCTION_TYPES,
    TEST_CALLS,
    JsModule,
    ancestors,
    enclosing,
    function_name,
    line,
    method_name,
    parameter_name,
    parameters,
    text,
)
from .models import Finding, Severity
from .style_common import (
    ALLOWED_SHORT_NAMES,
    aggregate_severity,
    listed,
    magic_numbers_finding,
    short_names_finding,
)

ALLOWED_NUMBERS = frozenset({"0", "1", "2", "10", "100", "1000", "0.5"})
MIN_DOCUMENTED_LENGTH = 15
MIN_COMMENTED_OUT_LINES = 2
_SORTERS = frozenset({"sort", "toSorted"})
_NAMED_NUMBER_PARENTS = frozenset(
    {"pair", "jsx_expression", "required_parameter", "optional_parameter", "enum_assignment"}
)
_CONSOLE_METHODS = frozenset({"log", "debug", "info", "trace"})
_SNAKE_CASE = re.compile(r"^[a-z]+(_[a-z0-9]+)+$")
_COMMENTED_CODE = re.compile(
    r"^//\s*(const|let|var|if|for|while|return|function|import|export|await|console\.)\b.*[;{(]"
)
_JSDOC_TYPES = re.compile(r"@(param|type|returns?|typedef)\b")


def _declared_identifiers(module: JsModule) -> Iterator[Node]:
    """Identifier nodes that introduce a name: variables, parameters and functions."""
    for declarator in module.nodes("variable_declarator"):
        target = declarator.child_by_field_name("name")
        if target is None:
            continue
        yield from [target] if target.type == "identifier" else _identifiers_in(target)
    for function in module.nodes(*FUNCTION_TYPES):
        name = function.child_by_field_name("name")
        if name is not None and name.type == "identifier":
            yield name
        if not _is_comparator(function):
            for parameter in parameters(function):
                target = parameter.child_by_field_name("pattern") or parameter
                if target.type == "identifier":
                    yield target


def _identifiers_in(pattern: Node) -> list[Node]:
    return [child for child in pattern.named_children if child.type == "identifier"]


def _is_comparator(function: Node) -> bool:
    """`(a, b) => …` passed to `.sort()` is the accepted idiom for comparators."""
    call = function.parent.parent if function.parent is not None else None
    return call is not None and call.type == "call_expression" and method_name(call) in _SORTERS


def check_names(module: JsModule) -> Iterator[Finding]:
    """Single-letter names, and snake_case in a camelCase language."""
    short: dict[str, int] = {}
    snake: dict[str, Node] = {}
    for identifier in _declared_identifiers(module):
        name = text(identifier)
        if len(name) == 1 and name not in ALLOWED_SHORT_NAMES:
            short.setdefault(name, line(identifier))
        elif _SNAKE_CASE.match(name):
            snake.setdefault(name, identifier)
    finding = short_names_finding(short, module.label)
    if finding is not None:
        yield finding
    if snake:
        message = f"snake_case names ({listed(snake)}); JavaScript convention is camelCase"
        first = next(iter(snake.values()))
        yield module.finding("naming-convention", Severity.INFO, message, first)


def _is_named_number(number: Node) -> bool:
    """Numbers that already have a name next to them: `width: 32`, `width={32}`, `MAX = 5`."""
    parent = number.parent
    if parent is None or parent.type in _NAMED_NUMBER_PARENTS:
        return True
    if parent.type == "subscript_expression":
        return True
    declarator = enclosing(number, {"variable_declarator"})
    return declarator is not None and text(declarator.child_by_field_name("name")).isupper()


def _is_in_test(node: Node) -> bool:
    """Inside a `describe`/`it`/`test` callback, where literal inputs and outputs belong."""
    return any(
        parent.type == "call_expression"
        and text(parent.child_by_field_name("function")).split(".")[0] in TEST_CALLS
        for parent in ancestors(node)
    )


def check_magic_numbers(module: JsModule) -> Iterator[Finding]:
    """Bare numbers inside functions, whose meaning the reader has to guess."""
    found = [
        (line(number), text(number))
        for number in module.nodes("number")
        if text(number) not in ALLOWED_NUMBERS
        and enclosing(number, FUNCTION_TYPES) is not None
        and not _is_named_number(number)
        and not _is_in_test(number)
    ]
    finding = magic_numbers_finding(found, module.label)
    if finding is not None:
        yield finding


def check_nested_ternaries(module: JsModule) -> Iterator[Finding]:
    """A ternary inside a ternary is an if/else chain that is hard to read."""
    for ternary in module.nodes("ternary_expression"):
        parent = ternary.parent
        while parent is not None and parent.type == "parenthesized_expression":
            parent = parent.parent
        if parent is not None and parent.type == "ternary_expression":
            message = "nested ternary; use if/else or a lookup"
            yield module.finding("nested-ternary", Severity.WARNING, message, ternary)


def check_console(module: JsModule) -> Iterator[Finding]:
    """Debug logging left in the code."""
    logs = [
        call
        for call in module.method_calls(*_CONSOLE_METHODS)
        if text(call.child_by_field_name("function").child_by_field_name("object")) == "console"
    ]
    if logs:
        message = f"{len(logs)} console logging call(s) left in code"
        yield module.finding("no-console", Severity.WARNING, message, logs[0])


def check_commented_out_code(module: JsModule) -> Iterator[Finding]:
    """Dead code kept in comments belongs in version control, not in the file."""
    dead = [comment for comment in module.nodes("comment") if _COMMENTED_CODE.match(text(comment))]
    if len(dead) >= MIN_COMMENTED_OUT_LINES:
        message = f"{len(dead)} lines of commented-out code; delete them (git remembers)"
        yield module.finding("commented-out-code", Severity.INFO, message, dead[0])


def _functions_with_parameters(module: JsModule) -> list[Node]:
    return [
        function
        for function in module.nodes(*FUNCTION_TYPES)
        if any(parameter_name(parameter) for parameter in parameters(function))
        and not _is_callback(function)
    ]


def _is_callback(function: Node) -> bool:
    """Functions whose parameter types come from context: callbacks, props, typed objects."""
    parent = function.parent
    if parent is None:
        return False
    if parent.type in ("arguments", "jsx_expression"):
        return True  # the callee, or the component's props, declare the parameter types
    declarator = enclosing(function, {"variable_declarator"}) if parent.type == "pair" else None
    return declarator is not None and declarator.child_by_field_name("type") is not None


def check_types(module: JsModule) -> Iterator[Finding]:
    """Plain JavaScript with no type information, or TypeScript parameters left untyped."""
    functions = _functions_with_parameters(module)
    if not functions:
        return
    if module.language == "javascript":
        has_jsdoc = any(_JSDOC_TYPES.search(text(comment)) for comment in module.nodes("comment"))
        if not has_jsdoc and not module.has("type_annotation"):
            message = "no type information; use TypeScript or JSDoc so callers know what to pass"
            yield module.finding("no-types", Severity.WARNING, message, functions[0])
        return
    untyped = [
        function
        for function in functions
        if any(_is_untyped(parameter) for parameter in parameters(function))
    ]
    if untyped:
        names = listed(function_name(function) for function in untyped)
        message = f"{len(untyped)} function(s) with untyped parameters ({names})"
        yield module.finding(
            "untyped-params", aggregate_severity(len(untyped)), message, untyped[0]
        )


def _is_untyped(parameter: Node) -> bool:
    if parameter.type not in ("required_parameter", "optional_parameter"):
        return False
    has_type = parameter.child_by_field_name("type") is not None
    has_default = parameter.child_by_field_name("value") is not None
    return not has_type and not has_default


def check_docs(module: JsModule) -> Iterator[Finding]:
    """Long exported functions with no comment explaining what they are for."""
    undocumented = [
        function
        for function in module.nodes(*FUNCTION_TYPES)
        if _is_exported(function) and _length(function) >= MIN_DOCUMENTED_LENGTH
        if not _has_leading_comment(function)
    ]
    if undocumented:
        names = listed(function_name(function) for function in undocumented)
        message = f"{len(undocumented)} exported function(s) without a doc comment ({names})"
        severity = aggregate_severity(len(undocumented))
        yield module.finding("missing-docs", severity, message, undocumented[0])


def _length(function: Node) -> int:
    return function.end_point[0] - function.start_point[0] + 1


def _is_exported(function: Node) -> bool:
    return any(parent.type == "export_statement" for parent in ancestors(function))


def _has_leading_comment(function: Node) -> bool:
    statement = function
    for parent in ancestors(function):
        if parent.type == "program":
            break
        statement = parent
    previous = statement.prev_named_sibling
    return previous is not None and previous.type == "comment"


STYLE_RULES: tuple[Callable[[JsModule], Iterator[Finding]], ...] = (
    check_names,
    check_magic_numbers,
    check_nested_ternaries,
    check_console,
    check_commented_out_code,
    check_types,
    check_docs,
)
