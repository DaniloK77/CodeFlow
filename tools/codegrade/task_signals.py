"""Static checks of a submission against its task and explanation. No AI involved.

These are signals, not a verdict: the names a task or an explanation mentions are looked up
in the code. They can show that `pair_sums(numbers, target)` was never defined, or that an
explanation talks about a `cache` the code doesn't have. They can't show that code is correct.
"""

from __future__ import annotations

import ast
import io
import re
import tokenize
from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from . import js_parser
from .assignment import Assignment, StaticCheck
from .source import SourceFile

MAX_CHECKS_PER_TEXT = 10
_NAME = r"[A-Za-z_$][\w$]*"
_BACKTICKED = re.compile(r"`([^`\n]{1,120})`")
_SIGNATURE = re.compile(rf"({_NAME})\s*(?:\(([^()]*)\))?\Z")
_CALL = re.compile(rf"(?<![\w.$`])({_NAME})\(([^()\n`]{{0,120}})\)")
_INTRODUCED = re.compile(rf"\b(?:called|named)\s+[\"'“‘]?({_NAME})")
# camelCase or snake_case in running text is almost always an identifier.
_CODE_LIKE = re.compile(
    r"(?<![\w$`.])([a-z][a-z0-9]*(?:[A-Z][a-z0-9]*)+|[a-z][a-z0-9]*(?:_[a-z0-9]+)+)(?![\w$(])"
)
# Words that look like names to a regex but are prose, literals or language keywords.
_STOP_WORDS = (
    "a an and as be by e for g i if in is it of on or s the to with when where which that this "
    "null undefined true false none nan function class return const let var def import export "
    "from new else while async await string number boolean int float str bool list dict array "
    "object void any"
)
_NOT_NAMES = frozenset(_STOP_WORDS.split())
_PLURAL_SUFFIXES = frozenset({"s", "es"})
_OPENERS, _CLOSERS = "([{", ")]}"


@dataclass(frozen=True)
class Mention:
    """A name a text refers to, with the argument count when it was written as a call."""

    name: str
    arguments: int | None = None


@dataclass(frozen=True)
class Definition:
    """A function, class or variable the code defines. ``most`` is None for variadic functions."""

    name: str
    path: str
    line: int
    least: int | None = None
    most: int | None = None
    callable: bool = False

    def accepts(self, arguments: int) -> bool:
        """Whether a call with this many arguments fits the parameter list."""
        if not self.callable or self.least is None:
            return True
        return self.least <= arguments and (self.most is None or arguments <= self.most)


def static_checks(assignment: Assignment, sources: Sequence[SourceFile]) -> tuple[StaticCheck, ...]:
    """Looks up the names the task and the explanation mention in the submitted code."""
    definitions = {definition.name: definition for definition in _all_definitions(sources)}
    identifiers = {name for source in sources for name in _identifiers(source)}
    task = [
        _task_check(mention, definitions, identifiers)
        for mention in mentions(assignment.task, introduced=True)
    ]
    explanation = [
        _explanation_check(mention, identifiers)
        for mention in mentions(assignment.explanation, introduced=False)
    ]
    return (*task[:MAX_CHECKS_PER_TEXT], *explanation[:MAX_CHECKS_PER_TEXT])


def mentions(text: str, *, introduced: bool) -> list[Mention]:
    """Code names in ``text``, in order of first appearance.

    ``introduced`` also accepts plain words that follow "called" or "named", which is how a
    task usually introduces what has to be built.
    """
    found: dict[str, Mention] = {}

    def add(name: str, arguments: str | None, position: int) -> None:
        if name.lower() in _NOT_NAMES or (arguments or "").strip() in _PLURAL_SUFFIXES:
            return
        count = None if arguments is None else _argument_count(arguments)
        known = found.get(name)
        if known is None or (known[1].arguments is None and count is not None):
            found[name] = (known[0] if known else position, Mention(name, count))

    for match in _BACKTICKED.finditer(text):
        signature = _SIGNATURE.match(match.group(1).strip())
        if signature is not None:
            add(signature.group(1), signature.group(2), match.start())
    for match in _CALL.finditer(text):
        add(match.group(1), match.group(2), match.start())
    for match in _CODE_LIKE.finditer(text):
        add(match.group(1), None, match.start())
    if introduced:
        for match in _INTRODUCED.finditer(text):
            add(match.group(1), None, match.start())
    return [mention for _, mention in sorted(found.values(), key=lambda item: item[0])]


def _argument_count(arguments: str) -> int | None:
    """Top-level comma-separated arguments; None when the list is elided (`...`)."""
    if "..." in arguments or "…" in arguments:
        return None
    if not arguments.strip():
        return 0
    depth, count = 0, 1
    for character in arguments:
        if character in _OPENERS:
            depth += 1
        elif character in _CLOSERS:
            depth -= 1
        elif character == "," and depth == 0:
            count += 1
    return count


def _task_check(
    mention: Mention, definitions: dict[str, Definition], identifiers: set[str]
) -> StaticCheck:
    name = mention.name
    definition = definitions.get(name)
    if definition is not None:
        where = f"{definition.path}:{definition.line}"
        if mention.arguments is not None and not definition.accepts(mention.arguments):
            detail = (
                f"defined at {where} with {_parameter_range(definition)}, "
                f"but the task uses {mention.arguments}"
            )
            return StaticCheck("task", name, "mismatch", detail)
        return StaticCheck("task", name, "found", f"defined at {where}")
    if name in identifiers:
        return StaticCheck("task", name, "found", "used in the code")
    similar = _similar(name, definitions)
    if similar is not None:
        detail = f"not defined; the code has `{similar.name}` at {similar.path}:{similar.line}"
        return StaticCheck("task", name, "mismatch", detail)
    return StaticCheck("task", name, "missing", "the task names it, the code doesn't define it")


def _explanation_check(mention: Mention, identifiers: set[str]) -> StaticCheck:
    if mention.name in identifiers:
        return StaticCheck("explanation", mention.name, "found", "appears in the code")
    detail = "the explanation mentions it, the code doesn't contain it"
    return StaticCheck("explanation", mention.name, "missing", detail)


def _parameter_range(definition: Definition) -> str:
    if definition.most is None:
        return f"at least {definition.least} parameter(s)"
    if definition.least == definition.most:
        return f"{definition.most} parameter(s)"
    return f"{definition.least} to {definition.most} parameters"


def _normalised(name: str) -> str:
    return name.replace("_", "").lower()


def _similar(name: str, definitions: dict[str, Definition]) -> Definition | None:
    """A definition that differs from ``name`` only in case or underscores."""
    wanted = _normalised(name)
    return next((d for d in definitions.values() if _normalised(d.name) == wanted), None)


def _all_definitions(sources: Sequence[SourceFile]) -> Iterator[Definition]:
    for source in sources:
        if source.language == "python":
            yield from _python_definitions(source)
        else:
            yield from _js_definitions(source)


def _python_definitions(source: SourceFile) -> Iterator[Definition]:
    try:
        tree = ast.parse(source.raw)
    except (SyntaxError, RecursionError, MemoryError, ValueError):
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            least, most = _python_parameter_range(node.args)
            yield Definition(node.name, source.label, node.lineno, least, most, callable=True)
        elif isinstance(node, ast.ClassDef):
            yield Definition(node.name, source.label, node.lineno)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    yield Definition(target.id, source.label, node.lineno)


def _python_parameter_range(arguments: ast.arguments) -> tuple[int, int | None]:
    positional = [*arguments.posonlyargs, *arguments.args]
    named = [argument for argument in positional if argument.arg not in ("self", "cls")]
    least = len(named) - len(arguments.defaults)
    most = None if arguments.vararg is not None else len(named) + len(arguments.kwonlyargs)
    return max(least, 0), most


def _js_definitions(source: SourceFile) -> Iterator[Definition]:
    for node in js_parser.walk(source.tree.root_node):
        if node.type in js_parser.FUNCTION_TYPES:
            name = js_parser.function_name(node)
            if name != "<anonymous>":
                least, most = _js_parameter_range(node)
                yield Definition(
                    name, source.label, js_parser.line(node), least, most, callable=True
                )
        elif node.type in ("class_declaration", "variable_declarator"):
            name_node = node.child_by_field_name("name")
            value = node.child_by_field_name("value")
            is_function = value is not None and value.type in js_parser.FUNCTION_TYPES
            if name_node is not None and name_node.type.endswith("identifier") and not is_function:
                yield Definition(js_parser.text(name_node), source.label, js_parser.line(node))


def _js_parameter_range(function: js_parser.Node) -> tuple[int, int | None]:
    parameters = js_parser.parameters(function)
    variadic = any("rest_pattern" in {child.type for child in p.children} for p in parameters)
    optional = sum(
        1
        for parameter in parameters
        if parameter.type == "optional_parameter"
        or parameter.child_by_field_name("value") is not None
    )
    most = None if variadic else len(parameters)
    return len(parameters) - optional - (1 if variadic else 0), most


def _identifiers(source: SourceFile) -> Iterator[str]:
    """Every identifier the code uses: names, properties, JSX tags and attributes."""
    if source.language != "python":
        for node in js_parser.walk(source.tree.root_node):
            if node.child_count == 0 and "identifier" in node.type:
                yield js_parser.text(node)
        return
    try:
        for token in tokenize.generate_tokens(io.StringIO(source.raw).readline):
            if token.type == tokenize.NAME:
                yield token.string
    except (tokenize.TokenError, SyntaxError, IndentationError):
        yield from re.findall(r"[A-Za-z_]\w*", source.raw)
