"""React and accessibility rules, checked on real JSX nodes."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass

from tree_sitter import Node

from .js_parser import (
    FUNCTION_TYPES,
    JSX_TAG_TYPES,
    JsModule,
    ancestors,
    enclosing,
    method_name,
    parameter_name,
    parameters,
    text,
)
from .models import Finding, Severity

_NON_INTERACTIVE = frozenset(
    {"div", "span", "li", "p", "td", "tr", "section", "article", "img", "ul", "h1", "h2", "h3"}
)
_FORM_FIELDS = frozenset({"input", "select", "textarea"})
_SELF_LABELLED_INPUTS = frozenset({"hidden", "submit", "button", "reset"})
_LABELLING_ATTRIBUTES = ("aria-label", "aria-labelledby", "id")
_RETURN_PATH = frozenset(
    {
        "parenthesized_expression",
        "return_statement",
        "statement_block",
        "ternary_expression",
        "binary_expression",
        "if_statement",
        "else_clause",
        "await_expression",
    }
)
_MUTATORS = ("push", "pop", "shift", "unshift", "splice", "sort", "reverse")
_SUBSCRIPTIONS = ("addEventListener", "subscribe", "on")
_EFFECT_HOOKS = ("useEffect", "useLayoutEffect", "React.useEffect")


@dataclass(frozen=True)
class Tag:
    """An opening or self-closing JSX tag with its attributes."""

    node: Node
    name: str
    attributes: dict[str, Node | None]
    has_spread: bool

    def value(self, attribute: str) -> str:
        """The literal value of an attribute, without quotes ("" when dynamic or absent)."""
        node = self.attributes.get(attribute)
        return text(node).strip("\"'") if node is not None and node.type == "string" else ""


def _tags(module: JsModule) -> Iterator[Tag]:
    for node in module.nodes(*JSX_TAG_TYPES):
        attributes: dict[str, Node | None] = {}
        for attribute in node.named_children:
            if attribute.type == "jsx_attribute":
                key, *value = attribute.named_children
                attributes[text(key)] = value[0] if value else None
        has_spread = any(child.type == "jsx_expression" for child in node.named_children)
        yield Tag(node, text(node.child_by_field_name("name")), attributes, has_spread)


def check_tags(module: JsModule) -> Iterator[Finding]:
    """Per-tag accessibility checks: images, buttons, dead links, fake buttons, labels."""
    for tag in _tags(module):
        if tag.has_spread:
            continue  # {...props} may provide anything; don't guess
        yield from _tag_findings(module, tag)


def _tag_findings(module: JsModule, tag: Tag) -> Iterator[Finding]:
    if tag.name == "img" and "alt" not in tag.attributes:
        message = '<img> without alt text (use alt="" if decorative)'
        yield module.finding("img-alt", Severity.ERROR, message, tag.node)
    if tag.name == "button" and "type" not in tag.attributes:
        message = '<button> without explicit type (defaults to "submit")'
        yield module.finding("button-type", Severity.WARNING, message, tag.node)
    if tag.value("href") == "#":
        message = 'dead link `href="#"`; use a real URL or a <button>'
        yield module.finding("placeholder-href", Severity.WARNING, message, tag.node)
    if (
        tag.name in _NON_INTERACTIVE
        and "onClick" in tag.attributes
        and "role" not in tag.attributes
    ):
        message = f"click handler on <{tag.name}>; keyboard users can't trigger it (use a <button>)"
        yield module.finding("click-non-interactive", Severity.WARNING, message, tag.node)
    if tag.name in _FORM_FIELDS and _is_unlabelled(tag):
        message = "form field without a label; add <label htmlFor> or aria-label"
        yield module.finding("input-label", Severity.WARNING, message, tag.node)


def _is_unlabelled(tag: Tag) -> bool:
    if tag.value("type") in _SELF_LABELLED_INPUTS:
        return False
    if any(name in tag.attributes for name in _LABELLING_ATTRIBUTES):
        return False
    wrappers = (parent for parent in ancestors(tag.node) if parent.type == "jsx_element")
    return not any(
        text(wrapper.child_by_field_name("open_tag").child_by_field_name("name")) == "label"
        for wrapper in wrappers
        if wrapper.child_by_field_name("open_tag") is not None
    )


def _map_callback(node: Node) -> Node | None:
    """The callback of the `.map(...)` call a node sits in, if any."""
    for parent in ancestors(node):
        if parent.type in FUNCTION_TYPES:
            call = parent.parent.parent if parent.parent is not None else None
            is_map = (
                call is not None and call.type == "call_expression" and method_name(call) == "map"
            )
            return parent if is_map else None
    return None


def check_keys(module: JsModule) -> Iterator[Finding]:
    """List items need a stable `key`: not missing, and not the array index."""
    for tag in _tags(module):
        callback = _map_callback(tag.node)
        if callback is None or not _is_callback_root(tag.node, callback):
            continue
        key = tag.attributes.get("key")
        index = parameters(callback)[1:2]
        index_name = parameter_name(index[0]) if index else None
        if "key" not in tag.attributes and not tag.has_spread:
            message = "list item rendered in `.map()` without a `key`"
            yield module.finding("missing-key", Severity.WARNING, message, tag.node)
        elif key is not None and index_name and text(key).strip("{} ") == index_name:
            message = f"array index `{index_name}` used as React key; use a stable id"
            yield module.finding("index-as-key", Severity.WARNING, message, tag.node)


def _is_callback_root(tag: Node, callback: Node) -> bool:
    """Whether a tag is the element the callback returns, not something nested inside it."""
    element = tag.parent if tag.type == "jsx_opening_element" else tag
    if element is None:
        return False
    outer = enclosing(element, {"jsx_element"})
    if outer is not None and _is_within(outer, callback):
        return False
    node = element.parent
    while node is not None and node != callback:
        if node.type not in _RETURN_PATH:
            return False  # e.g. a property of an object the callback returns
        node = node.parent
    return node is not None


def _is_within(node: Node, container: Node) -> bool:
    return container.start_byte <= node.start_byte and node.end_byte <= container.end_byte


def _effect_callbacks(module: JsModule) -> Iterator[Node]:
    for call in module.calls(*_EFFECT_HOOKS):
        arguments = call.child_by_field_name("arguments")
        first = arguments.named_children[0] if arguments and arguments.named_children else None
        if first is not None and first.type in FUNCTION_TYPES:
            yield first


def _calls_in(scope: Node) -> Iterator[Node]:
    stack = list(scope.children)
    while stack:
        node = stack.pop()
        if node.type == "call_expression":
            yield node
        stack.extend(node.children)


def _has_cleanup(callback: Node) -> bool:
    body = callback.child_by_field_name("body")
    if body is None or body.type != "statement_block":
        return False
    return any(child.type == "return_statement" and child.named_children for child in body.children)


def check_effects(module: JsModule) -> Iterator[Finding]:
    """Effects that subscribe or fetch need a cleanup function."""
    for callback in _effect_callbacks(module):
        if _has_cleanup(callback):
            continue
        calls = list(_calls_in(callback))
        callees = {text(call.child_by_field_name("function")) for call in calls}
        methods = {method_name(call) for call in calls}
        if methods & set(_SUBSCRIPTIONS) or "setInterval" in callees:
            message = "effect subscribes or starts a timer but returns no cleanup function"
            yield module.finding("effect-cleanup", Severity.WARNING, message, callback)
        elif "fetch" in callees and not module.has("new_expression"):
            message = (
                "effect fetches without a cleanup; a slow response can update an unmounted "
                "component or overwrite newer data (use AbortController)"
            )
            yield module.finding("effect-race", Severity.INFO, message, callback)


def _state_names(module: JsModule) -> set[str]:
    names: set[str] = set()
    for declarator in module.nodes("variable_declarator"):
        value = declarator.child_by_field_name("value")
        target = declarator.child_by_field_name("name")
        is_state = value is not None and value.type == "call_expression"
        is_state = is_state and text(value.child_by_field_name("function")).endswith("useState")
        if is_state and target is not None and target.type == "array_pattern":
            names.add(text(target.named_children[0]) if target.named_children else "")
    return names - {""}


def check_state_mutation(module: JsModule) -> Iterator[Finding]:
    """React state must be replaced, never changed in place."""
    state = _state_names(module)
    for call in module.method_calls(*_MUTATORS):
        receiver = call.child_by_field_name("function").child_by_field_name("object")
        if text(receiver) in state:
            message = f"`{text(receiver)}.{method_name(call)}()` mutates React state in place"
            yield module.finding("state-mutation", Severity.WARNING, message, call)
    for assignment in module.nodes("assignment_expression"):
        target = assignment.child_by_field_name("left")
        if target is not None and target.type in ("member_expression", "subscript_expression"):
            owner = text(target.child_by_field_name("object"))
            if owner in state:
                message = f"assignment into `{owner}` mutates React state in place"
                yield module.finding("state-mutation", Severity.WARNING, message, assignment)


JSX_RULES: tuple[Callable[[JsModule], Iterator[Finding]], ...] = (
    check_tags,
    check_keys,
    check_effects,
    check_state_mutation,
)
