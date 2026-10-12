"""Python readability and documentation rules: names, magic numbers, docstrings, hints.

Rules that would fire many times per file (one per name, number or function) are reported
as a single aggregated finding, so one habit can't sink an otherwise good file.
"""

from __future__ import annotations

import ast
from collections.abc import Iterator

from .models import Finding, Severity
from .style_common import (
    ALLOWED_SHORT_NAMES,
    aggregate_severity,
    magic_numbers_finding,
    short_names_finding,
)

FunctionNode = ast.FunctionDef | ast.AsyncFunctionDef

# Numbers that explain themselves (identity, halves, powers of ten).
ALLOWED_NUMBERS = frozenset({0, 1, 2, -1, 10, 100, 1000, 0.5})
MIN_DOCUMENTED_LENGTH = 5
_DEFINITIONS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def style_findings(tree: ast.Module, label: str) -> list[Finding]:
    """All readability and documentation findings for one parsed module."""
    findings = [
        *_short_name_findings(tree, label),
        *_magic_number_findings(tree, label),
        *_range_len_findings(tree, label),
        *_nested_loop_findings(tree, label),
        *_documentation_findings(tree, label),
        *_import_side_effect_findings(tree, label),
        *_naming_findings(tree, label),
    ]
    return findings


def _comprehension_targets(tree: ast.Module) -> set[int]:
    """ids of Name nodes bound by comprehensions, where short names are idiomatic."""
    targets: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.comprehension):
            targets.update(id(name) for name in ast.walk(node.target))
    return targets


def _short_name_findings(tree: ast.Module, label: str) -> list[Finding]:
    idiomatic = _comprehension_targets(tree)
    names: dict[str, int] = {}
    for node in ast.walk(tree):
        if id(node) in idiomatic:
            continue
        for name, line in _bound_names_of(node):
            if len(name) == 1 and name not in ALLOWED_SHORT_NAMES:
                names.setdefault(name, line)
    finding = short_names_finding(names, label)
    return [finding] if finding else []


def _bound_names_of(node: ast.AST) -> Iterator[tuple[str, int]]:
    if isinstance(node, _DEFINITIONS):
        yield node.name, node.lineno
    elif isinstance(node, ast.arg) and node.arg not in {"self", "cls"}:
        yield node.arg, node.lineno
    elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
        yield node.id, node.lineno


def _function_bodies(tree: ast.Module) -> Iterator[FunctionNode]:
    for node in ast.walk(tree):
        if isinstance(node, FunctionNode):
            yield node


def _magic_number_findings(tree: ast.Module, label: str) -> list[Finding]:
    found = [
        (node.lineno, repr(node.value)) for node in _body_constants(tree) if _is_magic(node.value)
    ]
    finding = magic_numbers_finding(found, label)
    return [finding] if finding else []


def _body_constants(tree: ast.Module) -> Iterator[ast.Constant]:
    """Literals written inside function bodies (parameter defaults are already named)."""
    for function in _function_bodies(tree):
        if function.name.startswith("test_"):
            continue  # literal inputs and expected values belong in tests
        for statement in function.body:
            if not isinstance(statement, ast.Assert):
                yield from (n for n in ast.walk(statement) if isinstance(n, ast.Constant))


def _is_magic(value: object) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return value not in ALLOWED_NUMBERS


def _range_len_findings(tree: ast.Module, label: str) -> list[Finding]:
    findings = []
    for node in ast.walk(tree):
        if _is_range_len(node):
            message = "`range(len(...))` loop; iterate directly or use `enumerate()`"
            findings.append(Finding("range-len", Severity.INFO, message, label, node.lineno))
    return findings


def _is_range_len(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "range"
        and len(node.args) == 1
        and isinstance(node.args[0], ast.Call)
        and isinstance(node.args[0].func, ast.Name)
        and node.args[0].func.id == "len"
    )


def _nested_loop_findings(tree: ast.Module, label: str) -> list[Finding]:
    """A ``for`` over a collection, inside a ``for`` over the same collection: O(n²) pairs."""
    message = "nested loops over the same collection (O(n²)); a set or dict lookup is often faster"
    lines = sorted(
        {inner.lineno for outer, inner in _loop_pairs(tree) if _same_iterable(outer, inner)}
    )
    return [Finding("nested-loops", Severity.INFO, message, label, line) for line in lines]


def _loop_pairs(
    tree: ast.Module,
) -> Iterator[tuple[ast.For | ast.AsyncFor, ast.For | ast.AsyncFor]]:
    for outer in ast.walk(tree):
        if isinstance(outer, (ast.For, ast.AsyncFor)):
            inner_loops = (node for node in ast.walk(outer) if node is not outer)
            yield from (
                (outer, inner)
                for inner in inner_loops
                if isinstance(inner, (ast.For, ast.AsyncFor))
            )


def _same_iterable(outer: ast.For | ast.AsyncFor, inner: ast.For | ast.AsyncFor) -> bool:
    return ast.dump(outer.iter) == ast.dump(inner.iter)


def _public_functions(tree: ast.Module) -> list[FunctionNode]:
    """Module- and class-level functions whose names don't start with an underscore."""
    candidates: list[FunctionNode] = []
    for node in tree.body:
        if isinstance(node, FunctionNode):
            candidates.append(node)
        elif isinstance(node, ast.ClassDef):
            candidates.extend(child for child in node.body if isinstance(child, FunctionNode))
    return [function for function in candidates if not function.name.startswith("_")]


def _documentation_findings(tree: ast.Module, label: str) -> list[Finding]:
    public = _public_functions(tree)
    sizable = [function for function in public if _length(function) >= MIN_DOCUMENTED_LENGTH]
    undocumented = [function for function in sizable if ast.get_docstring(function) is None]
    untyped = [function for function in public if not _is_fully_annotated(function)]
    findings = []
    if undocumented:
        findings.append(
            _listing_finding("missing-docstrings", "without a docstring", undocumented, label)
        )
    if untyped:
        findings.append(
            _listing_finding("missing-type-hints", "without full type hints", untyped, label)
        )
    return findings


def _length(function: FunctionNode) -> int:
    return (function.end_lineno or function.lineno) - function.lineno + 1


def _listing_finding(rule: str, problem: str, functions: list[FunctionNode], label: str) -> Finding:
    listed = ", ".join(f"`{function.name}`" for function in functions[:4])
    message = f"{len(functions)} public function(s) {problem} ({listed})"
    line = min(function.lineno for function in functions)
    return Finding(rule, aggregate_severity(len(functions)), message, label, line)


def _is_fully_annotated(function: FunctionNode) -> bool:
    args = [*function.args.posonlyargs, *function.args.args, *function.args.kwonlyargs]
    params_typed = all(arg.annotation is not None for arg in args if arg.arg not in {"self", "cls"})
    returns_typed = function.returns is not None or function.name == "__init__"
    return params_typed and returns_typed


def _import_side_effect_findings(tree: ast.Module, label: str) -> list[Finding]:
    calls = [
        statement
        for statement in tree.body
        if isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Call)
    ]
    if not calls:
        return []
    message = (
        f'{len(calls)} statement(s) run on import; move them under `if __name__ == "__main__":`'
    )
    return [Finding("import-side-effects", Severity.INFO, message, label, calls[0].lineno)]


def _naming_findings(tree: ast.Module, label: str) -> list[Finding]:
    """PEP 8 names: snake_case functions, CapWords classes."""
    odd: dict[str, int] = {}
    for node in ast.walk(tree):
        if (isinstance(node, FunctionNode) and node.name != node.name.lower()) or (
            isinstance(node, ast.ClassDef)
            and (node.name.lstrip("_")[:1].islower() or "_" in node.name.lstrip("_"))
        ):
            odd.setdefault(node.name, node.lineno)
    if not odd:
        return []
    listed = ", ".join(f"`{name}`" for name in sorted(odd))
    message = f"names that break PEP 8 ({listed}): functions are snake_case, classes CapWords"
    return [Finding("naming-convention", Severity.INFO, message, label, min(odd.values()))]
