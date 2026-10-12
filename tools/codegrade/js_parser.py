"""JavaScript/TypeScript parsing with tree-sitter, plus small helpers for walking the tree.

Everything JS-related in codegrade works on this concrete syntax tree. There are no regexes
over source text: a rule sees real call expressions, JSX attributes and scopes, and a file
that doesn't parse is reported as such.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import lru_cache

import tree_sitter_typescript
from tree_sitter import Language, Node, Parser, Tree

from .models import Finding, Severity

FUNCTION_TYPES = frozenset(
    {
        "function_declaration",
        "generator_function_declaration",
        "function_expression",
        "generator_function",
        "arrow_function",
        "method_definition",
    }
)
JSX_TAG_TYPES = frozenset({"jsx_opening_element", "jsx_self_closing_element"})
TEST_CALLS = ("describe", "it", "test")
TYPESCRIPT_ONLY_TYPES = frozenset(
    {
        "type_annotation",
        "interface_declaration",
        "type_alias_declaration",
        "as_expression",
        "satisfies_expression",
        "enum_declaration",
        "non_null_expression",
        "accessibility_modifier",
        "type_arguments",
    }
)


@lru_cache(maxsize=2)
def _parser(dialect: str) -> Parser:
    grammar = (
        tree_sitter_typescript.language_typescript()
        if dialect == "typescript"
        else tree_sitter_typescript.language_tsx()
    )
    return Parser(Language(grammar))


def parse(source: str, dialect: str = "tsx") -> Tree:
    """Parses JS, JSX, TS or TSX. The TSX grammar is a superset that covers all but pure TS."""
    return _parser(dialect).parse(source.encode("utf-8"))


def walk(node: Node) -> Iterator[Node]:
    """Every node under ``node`` (inclusive), depth first, without recursion."""
    stack = [node]
    while stack:
        current = stack.pop()
        yield current
        stack.extend(reversed(current.children))


def max_depth(tree: Tree) -> int:
    """How many levels deep the syntax tree goes, measured without recursion."""
    cursor = tree.walk()
    depth = deepest = 0
    while True:
        if cursor.goto_first_child():
            depth += 1
            deepest = max(deepest, depth)
            continue
        while not cursor.goto_next_sibling():
            if not cursor.goto_parent():
                return deepest
            depth -= 1


def text(node: Node | None) -> str:
    """Source text of a node ("" for a missing node)."""
    return node.text.decode("utf-8", errors="replace") if node is not None and node.text else ""


def line(node: Node) -> int:
    """1-based line on which a node starts."""
    return node.start_point[0] + 1


def ancestors(node: Node) -> Iterator[Node]:
    """Parents of a node, innermost first."""
    current = node.parent
    while current is not None:
        yield current
        current = current.parent


def enclosing(node: Node, types: frozenset[str] | set[str]) -> Node | None:
    """Nearest ancestor whose type is in ``types``."""
    return next((parent for parent in ancestors(node) if parent.type in types), None)


def error_ratio(tree: Tree, size: int) -> float:
    """Share of the source (0 to 1) that the parser could not make sense of."""
    if not tree.root_node.has_error:
        return 0.0
    broken = 0
    stack = [tree.root_node]
    while stack:
        current = stack.pop()
        if current.type == "ERROR" or current.is_missing:
            broken += max(1, current.end_byte - current.start_byte)
        elif current.has_error:
            stack.extend(current.children)
    return min(1.0, broken / max(size, 1))


@dataclass
class JsModule:
    """One parsed file with its nodes indexed by type, so each rule is a cheap lookup."""

    label: str
    language: str
    tree: Tree
    by_type: dict[str, list[Node]] = field(default_factory=lambda: defaultdict(list))

    @classmethod
    def build(cls, label: str, language: str, tree: Tree) -> JsModule:
        """Indexes every node of an already parsed tree."""
        module = cls(label=label, language=language, tree=tree)
        for node in walk(tree.root_node):
            if node.is_named:  # the keyword `number` and a numeric literal share a type name
                module.by_type[node.type].append(node)
        return module

    @property
    def root(self) -> Node:
        """The program node."""
        return self.tree.root_node

    def nodes(self, *types: str) -> Iterator[Node]:
        """All nodes of the given types, in source order per type."""
        for node_type in types:
            yield from self.by_type.get(node_type, ())

    def has(self, *types: str) -> bool:
        """Whether any node of the given types exists."""
        return any(self.by_type.get(node_type) for node_type in types)

    def calls(self, *names: str) -> Iterator[Node]:
        """Call expressions whose callee is one of ``names`` (`fetch`, `JSON.parse`, …)."""
        wanted = set(names)
        for call in self.nodes("call_expression"):
            if text(call.child_by_field_name("function")) in wanted:
                yield call

    def method_calls(self, *methods: str) -> Iterator[Node]:
        """Call expressions of the form ``<anything>.method(...)``."""
        wanted = set(methods)
        for call in self.nodes("call_expression"):
            if method_name(call) in wanted:
                yield call

    def finding(self, rule: str, severity: Severity, message: str, node: Node) -> Finding:
        """A finding located at ``node``."""
        return Finding(rule, severity, message, self.label, line(node))


def method_name(call: Node) -> str | None:
    """`then` for `promise.then(...)`; None when the callee isn't a member access."""
    callee = call.child_by_field_name("function")
    if callee is None or callee.type != "member_expression":
        return None
    return text(callee.child_by_field_name("property"))


def function_name(node: Node) -> str:
    """The name a function is known by: its own, or the variable/property it is assigned to."""
    own = node.child_by_field_name("name")
    if own is not None:
        return text(own)
    parent = node.parent
    if parent is not None and parent.type in (
        "variable_declarator",
        "pair",
        "assignment_expression",
    ):
        label = parent.child_by_field_name("name") or parent.child_by_field_name("key")
        label = label or parent.child_by_field_name("left")
        if label is not None and label.type in ("identifier", "property_identifier"):
            return text(label)
    return "<anonymous>"


def parameters(function: Node) -> list[Node]:
    """Parameter nodes of a function (one node per parameter, patterns included)."""
    single = function.child_by_field_name("parameter")
    if single is not None:
        return [single]
    formal = function.child_by_field_name("parameters")
    return list(formal.named_children) if formal is not None else []


def parameter_name(parameter: Node) -> str | None:
    """`id` for `id`, `id: string` or `id = 1`; None for destructured or rest parameters."""
    target = parameter.child_by_field_name("pattern") or parameter
    return text(target) if target.type == "identifier" else None
