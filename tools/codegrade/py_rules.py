"""Reliability rules for Python, checked on the real AST.

Per-node rules live in one table. Rules that need context (scopes, parents, whole-module
name usage) are separate functions. Aggregated rules report once per file, with a count.
"""

from __future__ import annotations

import ast
from collections.abc import Callable, Iterator
from itertools import pairwise

from .models import Finding, Severity
from .style_common import SECRET_NAME, aggregate_severity, is_secret_value, listed

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef

_MUTABLE_DEFAULTS = (ast.List, ast.Dict, ast.Set)
_HTTP_METHODS = frozenset({"get", "post", "put", "delete", "patch", "head", "request"})
_SQL_METHODS = frozenset({"execute", "executemany"})
_TERMINATORS = (ast.Return, ast.Raise, ast.Continue, ast.Break)
_DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
_SHADOWABLE_BUILTINS = frozenset(
    {
        "list", "dict", "set", "str", "int", "float", "bool", "tuple", "id", "input", "type",
        "sum", "max", "min", "len", "filter", "map", "object", "next", "all", "any",
        "dir", "format", "hash", "iter", "range", "print", "open", "vars", "bytes",
    }
)  # fmt: skip


def _is_requests_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "requests"
        and node.func.attr in _HTTP_METHODS
    )


def _is_bare_except(node: ast.AST) -> bool:
    return isinstance(node, ast.ExceptHandler) and node.type is None


def _is_swallowed(node: ast.AST) -> bool:
    if not isinstance(node, ast.ExceptHandler) or node.type is None:
        return False
    return all(_is_noop(statement) for statement in node.body)


def _is_noop(statement: ast.stmt) -> bool:
    is_ellipsis = isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)
    return isinstance(statement, (ast.Pass, ast.Continue)) or is_ellipsis


_REPORTING_CALLS = frozenset(
    {"exception", "error", "warning", "critical", "format_exc", "print_exc"}
)


def _reports_the_error(handler: ast.ExceptHandler) -> bool:
    """Whether the handler re-raises, logs or records the traceback instead of hiding it."""
    for child in ast.walk(handler):
        if isinstance(child, ast.Raise):
            return True
        if isinstance(child, ast.Call):
            name = child.func.attr if isinstance(child.func, ast.Attribute) else ""
            if name in _REPORTING_CALLS:
                return True
    return False


def _is_broad_except(node: ast.AST) -> bool:
    if not isinstance(node, ast.ExceptHandler) or not isinstance(node.type, ast.Name):
        return False
    is_broad = node.type.id in {"Exception", "BaseException"}
    return is_broad and not _reports_the_error(node) and not _is_swallowed(node)


def _is_eval(node: ast.AST) -> bool:
    is_call = isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    return is_call and node.func.id in {"eval", "exec"}


def _has_mutable_default(node: ast.AST) -> bool:
    if not isinstance(node, FunctionNode):
        return False
    defaults = [*node.args.defaults, *node.args.kw_defaults]
    return any(isinstance(default, _MUTABLE_DEFAULTS) for default in defaults)


def _compares_with(node: ast.AST, *values: object) -> bool:
    if not isinstance(node, ast.Compare):
        return False
    uses_equality = any(isinstance(operator, (ast.Eq, ast.NotEq)) for operator in node.ops)
    return uses_equality and any(
        isinstance(side, ast.Constant) and any(side.value is value for value in values)
        for side in (node.left, *node.comparators)
    )


def _is_shell_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    is_os_system = isinstance(func, ast.Attribute) and func.attr == "system"
    uses_shell = any(
        keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value
        for keyword in node.keywords
    )
    return is_os_system or uses_shell


def _is_built_sql(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr not in _SQL_METHODS or not node.args:
        return False
    query = node.args[0]
    is_format = (
        isinstance(query, ast.Call)
        and isinstance(query.func, ast.Attribute)
        and query.func.attr == "format"
    )
    return isinstance(query, (ast.JoinedStr, ast.BinOp)) or is_format


def _lacks_timeout(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call) or not _is_requests_call(node):
        return False
    return not any(keyword.arg == "timeout" for keyword in node.keywords)


def _is_hardcoded_secret(node: ast.AST) -> bool:
    if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Constant):
        return False
    value = node.value.value
    names = [target.id for target in node.targets if isinstance(target, ast.Name)]
    return (
        isinstance(value, str)
        and is_secret_value(value)
        and any(SECRET_NAME.search(name) for name in names)
    )


NODE_RULES: tuple[tuple[Callable[[ast.AST], bool], str, Severity, str], ...] = (
    (_is_eval, "no-eval", Severity.ERROR, "eval()/exec() executes arbitrary code"),
    (
        _is_built_sql,
        "sql-injection",
        Severity.ERROR,
        "SQL built with string formatting; pass parameters to execute() instead",
    ),
    (
        _is_hardcoded_secret,
        "hardcoded-secret",
        Severity.ERROR,
        "looks like a hardcoded secret; load it from the environment",
    ),
    (
        _is_shell_call,
        "shell-injection",
        Severity.WARNING,
        "runs a shell command; pass an argument list without shell=True",
    ),
    (
        _is_bare_except,
        "bare-except",
        Severity.WARNING,
        "bare `except:` also catches KeyboardInterrupt",
    ),
    (
        _is_swallowed,
        "swallowed-exception",
        Severity.WARNING,
        "exception caught and ignored; handle it, log it or let it propagate",
    ),
    (
        _is_broad_except,
        "broad-except",
        Severity.INFO,
        "`except Exception` hides unexpected bugs; catch the errors you expect",
    ),
    (
        _has_mutable_default,
        "mutable-default",
        Severity.WARNING,
        "mutable default argument is shared across calls",
    ),
    (
        lambda node: isinstance(node, ast.Global),
        "no-global",
        Severity.WARNING,
        "`global` state makes code hard to test",
    ),
    (
        lambda node: _compares_with(node, None),
        "compare-to-none",
        Severity.WARNING,
        "comparison with `== None`; use `is None`",
    ),
    (
        lambda node: _compares_with(node, True, False),
        "compare-to-bool",
        Severity.INFO,
        "comparison with `== True/False`; use the value itself",
    ),
    (
        _lacks_timeout,
        "request-without-timeout",
        Severity.WARNING,
        "HTTP request without `timeout=`; it can hang forever",
    ),
    (
        lambda node: (
            isinstance(node, ast.ImportFrom) and any(alias.name == "*" for alias in node.names)
        ),
        "wildcard-import",
        Severity.WARNING,
        "wildcard import hides where names come from",
    ),
)


def reliability_findings(tree: ast.Module, label: str) -> list[Finding]:
    """Every reliability finding for one parsed module."""
    findings = [
        Finding(rule, severity, message, label, getattr(node, "lineno", 1))
        for node in ast.walk(tree)
        for matches, rule, severity, message in NODE_RULES
        if matches(node)
    ]
    for check in (_open_without_with, _unreachable, _unchecked_responses):
        findings.extend(check(tree, label))
    if not label.endswith("__init__.py"):
        findings.extend(_unused_imports(tree, label))
    findings.extend(_unused_variables(tree, label))
    findings.extend(_shadowed_builtins(tree, label))
    return findings


def _open_without_with(tree: ast.Module, label: str) -> Iterator[Finding]:
    managed = {
        id(item.context_expr)
        for node in ast.walk(tree)
        if isinstance(node, (ast.With, ast.AsyncWith))
        for item in node.items
    }
    for node in ast.walk(tree):
        is_open = isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        if is_open and node.func.id == "open" and id(node) not in managed:
            message = "`open()` without `with`; the file may never be closed"
            yield Finding("open-without-with", Severity.WARNING, message, label, node.lineno)


def _bodies(tree: ast.Module) -> Iterator[list[ast.stmt]]:
    for node in ast.walk(tree):
        for name in ("body", "orelse", "finalbody"):
            body = getattr(node, name, None)
            if isinstance(body, list) and body and isinstance(body[0], ast.stmt):
                yield body


def _unreachable(tree: ast.Module, label: str) -> Iterator[Finding]:
    for body in _bodies(tree):
        for previous, current in pairwise(body):
            if isinstance(previous, _TERMINATORS):
                keyword = type(previous).__name__.lower()
                message = f"unreachable code after `{keyword}`"
                yield Finding("unreachable-code", Severity.WARNING, message, label, current.lineno)
                break


def _unchecked_responses(tree: ast.Module, label: str) -> Iterator[Finding]:
    """`response.json()` on an HTTP response whose status was never checked."""
    for function in ast.walk(tree):
        if not isinstance(function, FunctionNode):
            continue
        nodes = list(ast.walk(function))
        request = next((node for node in nodes if _is_requests_call(node)), None)
        attributes = {node.attr for node in nodes if isinstance(node, ast.Attribute)}
        if request is not None and not attributes & {"raise_for_status", "status_code", "ok"}:
            message = "HTTP response used without `raise_for_status()` or a status check"
            line = getattr(request, "lineno", function.lineno)
            yield Finding("unchecked-response", Severity.WARNING, message, label, line)


def _loaded_names(tree: ast.AST) -> set[str]:
    names = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    attribute_roots = {
        node.value.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
    }
    return names | attribute_roots


def _exported_names(tree: ast.Module) -> set[str]:
    """Names listed in ``__all__`` (re-exports are not unused imports)."""
    exported: set[str] = set()
    for node in tree.body:
        is_all = isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        )
        if is_all and isinstance(node.value, (ast.List, ast.Tuple)):
            exported.update(
                item.value for item in node.value.elts if isinstance(item, ast.Constant)
            )
    return exported


def _unused_imports(tree: ast.Module, label: str) -> Iterator[Finding]:
    used = _loaded_names(tree) | _exported_names(tree)
    unused: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                name = (alias.asname or alias.name).split(".")[0]
                if name != "*" and name not in used:
                    unused.append((name, node.lineno))
    if unused:
        message = f"{len(unused)} unused import(s): {listed(name for name, _ in unused)}"
        yield Finding("unused-import", Severity.WARNING, message, label, unused[0][1])


def _unused_variables(tree: ast.Module, label: str) -> Iterator[Finding]:
    unused: list[tuple[str, int]] = []
    for function in ast.walk(tree):
        if not isinstance(function, FunctionNode):
            continue
        loaded = _loaded_names(function)
        declared_elsewhere = {
            name
            for node in ast.walk(function)
            if isinstance(node, (ast.Global, ast.Nonlocal))
            for name in node.names
        }
        for node in ast.walk(function):
            is_store = isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)
            if (
                is_store
                and node.id not in loaded | declared_elsewhere
                and not node.id.startswith("_")
            ):
                unused.append((node.id, node.lineno))
    if unused:
        names = listed(name for name, _ in unused)
        message = f"{len(set(unused))} variable(s) assigned but never used: {names}"
        yield Finding(
            "unused-variable", aggregate_severity(len(unused)), message, label, unused[0][1]
        )


def _shadowed_builtins(tree: ast.Module, label: str) -> Iterator[Finding]:
    shadowed: dict[str, int] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            name, line = node.arg, node.lineno
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            name, line = node.id, node.lineno
        elif isinstance(node, _DEFINITIONS):
            name, line = node.name, node.lineno
        else:
            continue
        if name in _SHADOWABLE_BUILTINS:
            shadowed.setdefault(name, line)
    if shadowed:
        message = f"shadows built-in name(s): {listed(sorted(shadowed))}"
        yield Finding("shadowed-builtin", Severity.WARNING, message, label, min(shadowed.values()))
