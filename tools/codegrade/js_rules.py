"""Reliability rules for JavaScript/TypeScript: bugs, risky constructs, unhandled failures.

Each rule is a small function over a parsed :class:`JsModule`. Rules that could fire many
times in one file (unused names, `any`) report once, with a count.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable, Iterator
from itertools import pairwise

from tree_sitter import Node

from .js_parser import FUNCTION_TYPES, JsModule, ancestors, enclosing, method_name, text
from .models import Finding, Severity
from .style_common import SECRET_NAME, aggregate_severity, is_secret_value, listed

_TERMINATORS = frozenset(
    {"return_statement", "throw_statement", "break_statement", "continue_statement"}
)
_HOISTED = frozenset({"function_declaration", "generator_function_declaration", "comment"})
_REFERENCE_TYPES = frozenset(
    {"identifier", "type_identifier", "shorthand_property_identifier", "jsx_identifier"}
)
_RAW_HTML_PROPERTIES = frozenset({"innerHTML", "outerHTML"})
_TODO = re.compile(r"\b(?:TODO|FIXME|HACK|XXX)\b")
_IGNORED_UNUSED = frozenset({"React"})


def check_debugger(module: JsModule) -> Iterator[Finding]:
    """`debugger` freezes the page for anyone with DevTools open."""
    for node in module.nodes("debugger_statement"):
        yield module.finding(
            "no-debugger", Severity.ERROR, "`debugger` statement left in code", node
        )


def check_eval(module: JsModule) -> Iterator[Finding]:
    """`eval()` and `new Function()` run arbitrary strings as code."""
    for call in module.calls("eval"):
        yield module.finding("no-eval", Severity.ERROR, "`eval()` executes arbitrary code", call)
    for node in module.nodes("new_expression"):
        if text(node.child_by_field_name("constructor")) == "Function":
            yield module.finding(
                "no-eval", Severity.ERROR, "`new Function()` executes arbitrary code", node
            )


def check_var(module: JsModule) -> Iterator[Finding]:
    """`var` is function-scoped and hoisted."""
    for node in module.nodes("variable_declaration"):
        message = "`var` is function-scoped; use `const` or `let`"
        yield module.finding("no-var", Severity.WARNING, message, node)


def check_loose_equality(module: JsModule) -> Iterator[Finding]:
    """`==` coerces types. Comparing with `null` is the one accepted idiom."""
    for node in module.nodes("binary_expression"):
        operator = node.child_by_field_name("operator")
        if operator is None or operator.type not in ("==", "!="):
            continue
        sides = (node.child_by_field_name("left"), node.child_by_field_name("right"))
        if not any(side is not None and side.type == "null" for side in sides):
            message = "loose equality; use `===` / `!==`"
            yield module.finding("eqeqeq", Severity.WARNING, message, node)


def check_empty_catch(module: JsModule) -> Iterator[Finding]:
    """An empty `catch` hides the failure completely."""
    for node in module.nodes("catch_clause"):
        body = node.child_by_field_name("body")
        if body is not None and not body.named_children:
            message = "empty catch block silently swallows errors"
            yield module.finding("empty-catch", Severity.WARNING, message, node)


def check_hardcoded_secret(module: JsModule) -> Iterator[Finding]:
    """A key, token or password written into the source ends up in version control."""
    for node in module.nodes("variable_declarator", "pair", "assignment_expression"):
        name = node.child_by_field_name("name") or node.child_by_field_name("key")
        name = name or node.child_by_field_name("left")
        value = node.child_by_field_name("value") or node.child_by_field_name("right")
        if name is None or value is None or value.type != "string":
            continue
        if SECRET_NAME.search(text(name)) and is_secret_value(text(value).strip("\"'`")):
            message = f"`{text(name)}` looks like a hardcoded secret; load it from the environment"
            yield module.finding("hardcoded-secret", Severity.ERROR, message, node)


def check_raw_html(module: JsModule) -> Iterator[Finding]:
    """Writing HTML strings into the DOM bypasses escaping (XSS)."""
    message = "raw HTML written to the DOM is an XSS risk"
    for attribute in module.nodes("jsx_attribute"):
        if text(attribute.named_children[0]) == "dangerouslySetInnerHTML":
            yield module.finding("dangerous-html", Severity.WARNING, message, attribute)
    for node in module.nodes("assignment_expression"):
        target = node.child_by_field_name("left")
        is_member = target is not None and target.type == "member_expression"
        if is_member and text(target.child_by_field_name("property")) in _RAW_HTML_PROPERTIES:
            yield module.finding("dangerous-html", Severity.WARNING, message, node)


def check_comments(module: JsModule) -> Iterator[Finding]:
    """Markers in comments: suppressed type errors, disabled lint rules, open TODOs."""
    for comment in module.nodes("comment"):
        body = text(comment)
        if "@ts-ignore" in body or "@ts-nocheck" in body:
            message = "type error suppressed with @ts-ignore / @ts-nocheck"
            yield module.finding("ts-suppression", Severity.WARNING, message, comment)
        if "eslint-disable" in body:
            message = "lint rule disabled inline"
            yield module.finding("lint-suppression", Severity.INFO, message, comment)
        if _TODO.search(body):
            message = "unresolved TODO / FIXME marker"
            yield module.finding("todo-comment", Severity.INFO, message, comment)


def check_unreachable(module: JsModule) -> Iterator[Finding]:
    """Statements after `return`, `throw`, `break` or `continue` never run."""
    for block in module.nodes("statement_block", "switch_case", "switch_default", "program"):
        statements = [child for child in block.named_children if child.type not in _HOISTED]
        for previous, current in pairwise(statements):
            if previous.type in _TERMINATORS:
                message = f"unreachable code after `{previous.type.split('_')[0]}`"
                yield module.finding("unreachable-code", Severity.WARNING, message, current)
                break


def _scope(node: Node, module: JsModule) -> Node:
    return enclosing(node, FUNCTION_TYPES) or module.root


def _property_names(scope: Node) -> set[str]:
    return {text(node) for node in _descendants(scope, "property_identifier")}


def _descendants(scope: Node, node_type: str) -> Iterator[Node]:
    stack = [scope]
    while stack:
        node = stack.pop()
        if node.type == node_type:
            yield node
        stack.extend(node.children)


def _is_handed_to_caller(call: Node) -> bool:
    """`return fetch(…)` and `() => fetch(…)`: the caller gets the response and checks it."""
    parent = call.parent
    if parent is not None and parent.type == "await_expression":
        parent = parent.parent
    return parent is not None and (
        parent.type == "return_statement"
        or (parent.type == "arrow_function" and parent.child_by_field_name("body") is not None)
    )


def check_unchecked_response(module: JsModule) -> Iterator[Finding]:
    """`fetch()` resolves on HTTP 404 and 500 too; the status has to be checked."""
    reported: set[int] = set()
    for call in module.calls("fetch", "window.fetch"):
        scope = _scope(call, module)
        if _is_handed_to_caller(call) or scope.id in reported:
            continue
        if _property_names(scope) & {"ok", "status"}:
            continue
        reported.add(scope.id)
        message = "`fetch()` result is used without checking `response.ok`"
        yield module.finding("unchecked-response", Severity.WARNING, message, call)


def _chain_handlers(call: Node) -> tuple[Node, set[str]]:
    """The outermost call of a `.then().then()` chain and the ways it handles rejection.

    "catch" for `.catch()`, "then" for a `.then(onFulfilled, onRejected)`.
    """
    top, handlers = call, set()
    while True:
        arguments = top.child_by_field_name("arguments")
        name = method_name(top)
        if name == "catch":
            handlers.add("catch")
        elif name == "then" and arguments is not None and arguments.named_child_count >= 2:
            handlers.add("then")
        parent = top.parent
        outer = parent.parent if parent is not None and parent.type == "member_expression" else None
        if outer is None or outer.type != "call_expression":
            return top, handlers
        top = outer


def check_unhandled_rejection(module: JsModule) -> Iterator[Finding]:
    """A promise chain with no rejection handler and no surrounding `try` loses its errors."""
    reported: set[int] = set()
    for call in module.method_calls("then"):
        top, handlers = _chain_handlers(call)
        handled = bool(handlers) or enclosing(top, {"try_statement"}) is not None
        is_statement = top.parent is not None and top.parent.type == "expression_statement"
        if handled or not is_statement or top.id in reported:
            continue
        reported.add(top.id)
        message = "promise chain without `.catch()`; a failure would go unnoticed"
        yield module.finding("unhandled-rejection", Severity.WARNING, message, top)


def check_json_parse(module: JsModule) -> Iterator[Finding]:
    """`JSON.parse` throws on malformed input."""
    for call in module.calls("JSON.parse"):
        if enclosing(call, {"try_statement"}) is None:
            message = "`JSON.parse()` outside try/catch throws on malformed input"
            yield module.finding("unguarded-json-parse", Severity.INFO, message, call)


def check_listener_cleanup(module: JsModule) -> Iterator[Finding]:
    """Outside React effects: more listeners added than removed suggests a leak."""
    if next(module.calls("useEffect", "React.useEffect"), None) is not None:
        return  # effects are checked precisely by `effect-cleanup`
    added = list(module.method_calls("addEventListener"))
    removed = list(module.method_calls("removeEventListener"))
    if len(added) > len(removed):
        message = "addEventListener without a matching removeEventListener (possible leak)"
        yield module.finding("listener-cleanup", Severity.WARNING, message, added[0])


def check_typescript_escapes(module: JsModule) -> Iterator[Finding]:
    """`any` and `!` both tell the compiler to stop checking."""
    anys = [node for node in module.nodes("predefined_type") if text(node) == "any"]
    if anys:
        message = f"`any` used {len(anys)} time(s); it switches off type checking"
        yield module.finding("no-explicit-any", Severity.WARNING, message, anys[0])
    assertions = list(module.nodes("non_null_expression"))
    if assertions:
        message = f"{len(assertions)} non-null assertion(s) (`!`); handle the null case instead"
        yield module.finding("non-null-assertion", Severity.INFO, message, assertions[0])


def _is_exported(node: Node) -> bool:
    return any(parent.type == "export_statement" for parent in ancestors(node))


def _declared_names(module: JsModule) -> Iterator[tuple[str, Node, bool]]:
    """(name, node, is_import) for imports and non-exported local declarations."""
    for specifier in module.nodes("import_specifier", "namespace_import"):
        name = specifier.child_by_field_name("alias") or specifier.named_children[-1]
        yield text(name), name, True
    for clause in module.nodes("import_clause"):
        for child in clause.named_children:
            if child.type == "identifier":
                yield text(child), child, True
    for declarator in module.nodes("variable_declarator"):
        target = declarator.child_by_field_name("name")
        if target is not None and target.type == "identifier" and not _is_exported(declarator):
            yield text(target), target, False


def check_unused(module: JsModule) -> Iterator[Finding]:
    """Imports and variables that are declared and never used again."""
    uses = Counter(text(node) for node in module.nodes(*_REFERENCE_TYPES))
    unused: dict[bool, list[tuple[str, Node]]] = {True: [], False: []}
    for name, node, is_import in _declared_names(module):
        if uses[name] <= 1 and not name.startswith("_") and name not in _IGNORED_UNUSED:
            unused[is_import].append((name, node))
    for is_import, rule, noun in (
        (True, "unused-import", "import"),
        (False, "unused-variable", "variable"),
    ):
        names = unused[is_import]
        if names:
            severity = Severity.WARNING if is_import else aggregate_severity(len(names))
            message = f"{len(names)} unused {noun}(s): {listed(name for name, _ in names)}"
            yield module.finding(rule, severity, message, names[0][1])


JS_RULES: tuple[Callable[[JsModule], Iterator[Finding]], ...] = (
    check_debugger,
    check_eval,
    check_var,
    check_loose_equality,
    check_empty_catch,
    check_hardcoded_secret,
    check_raw_html,
    check_comments,
    check_unreachable,
    check_unchecked_response,
    check_unhandled_rejection,
    check_json_parse,
    check_listener_cleanup,
    check_typescript_escapes,
    check_unused,
)
