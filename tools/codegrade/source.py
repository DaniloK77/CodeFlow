"""Source files and the facts every analyzer needs about them."""

from __future__ import annotations

import io
import re
import tokenize
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

from tree_sitter import Tree

from . import js_parser

JS_EXTENSIONS = frozenset({".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"})
TS_EXTENSIONS = frozenset({".ts", ".tsx"})
PY_EXTENSIONS = frozenset({".py"})
SUPPORTED_EXTENSIONS = JS_EXTENSIONS | PY_EXTENSIONS
_TEST_FILE = re.compile(r"(\.(test|spec)\.[cm]?[jt]sx?$)|(^test_.*\.py$)|(_test\.py$)")
_TEST_DIRECTORIES = frozenset({"tests", "test", "__tests__"})
# Leaves that carry no code of their own: comments and the bodies of string literals.
_NON_CODE_LEAVES = frozenset({"comment", "string_fragment"})
_NON_CODE_TOKENS = frozenset(
    {
        tokenize.COMMENT,
        tokenize.NL,
        tokenize.NEWLINE,
        tokenize.INDENT,
        tokenize.DEDENT,
        tokenize.ENCODING,
        tokenize.ENDMARKER,
    }
)


def language_of(path: Path) -> str | None:
    """ "typescript", "javascript" or "python" by file extension; None if unsupported."""
    suffix = path.suffix.lower()
    if suffix in TS_EXTENSIONS:
        return "typescript"
    if suffix in JS_EXTENSIONS:
        return "javascript"
    if suffix in PY_EXTENSIONS:
        return "python"
    return None


def is_test_file(name: str) -> bool:
    """Test modules and their helpers: `*.test.ts`, `test_*.py`, or anything under tests/."""
    parts = name.split("/")
    in_test_directory = any(part in _TEST_DIRECTORIES for part in parts[:-1])
    return (
        in_test_directory or parts[-1] == "conftest.py" or _TEST_FILE.search(parts[-1]) is not None
    )


def display_path(path: Path, root: Path) -> str:
    """``path`` relative to ``root`` in POSIX form, or as given if it lies outside."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


@dataclass
class SourceFile:
    label: str
    language: str
    raw: str

    @classmethod
    def from_text(cls, label: str, raw: str) -> SourceFile | None:
        """Builds a source from in-memory text; the label's extension selects the language."""
        language = language_of(Path(label))
        return None if language is None else cls(label=label, language=language, raw=raw)

    @classmethod
    def load(cls, path: Path, root: Path) -> SourceFile | None:
        """Reads a file from disk; None for unsupported file types."""
        if language_of(path) is None:
            return None
        raw = path.read_text(encoding="utf-8", errors="replace")
        return cls.from_text(display_path(path, root), raw)

    @cached_property
    def lines(self) -> list[str]:
        """The file split into lines (index 0 is line 1)."""
        return self.raw.split("\n")

    @cached_property
    def tree(self) -> Tree:
        """The tree-sitter syntax tree (JavaScript/TypeScript files only)."""
        dialect = "typescript" if self.label.lower().endswith(".ts") else "tsx"
        return js_parser.parse(self.raw, dialect)

    @cached_property
    def code_line_numbers(self) -> frozenset[int]:
        """1-based numbers of lines that hold code, not only comments or string bodies."""
        if self.language == "python":
            return _python_code_lines(self.raw)
        return frozenset(
            node.start_point[0] + 1
            for node in js_parser.walk(self.tree.root_node)
            if node.child_count == 0 and node.type not in _NON_CODE_LEAVES
        )

    @property
    def code_lines(self) -> int:
        """How many lines hold code."""
        return len(self.code_line_numbers)


def _python_code_lines(source: str) -> frozenset[int]:
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, SyntaxError, IndentationError):
        lines = enumerate(source.split("\n"), start=1)
        return frozenset(
            n for n, text in lines if text.strip() and not text.lstrip().startswith("#")
        )

    numbers: set[int] = set()
    previous = tokenize.NEWLINE
    for token in tokens:
        is_docstring = token.type == tokenize.STRING and previous in (
            tokenize.NEWLINE,
            tokenize.INDENT,
            tokenize.DEDENT,
        )
        if token.type not in _NON_CODE_TOKENS and not is_docstring:
            numbers.add(token.start[0])
        if token.type not in (tokenize.NL, tokenize.COMMENT):
            previous = token.type
    return frozenset(numbers)
