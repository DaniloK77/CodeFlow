"""Decides what a pasted snippet is, and whether it can be graded at all.

A grader that scores plain English or Java as "100/100 JavaScript" is worse than useless, so
input is checked before any rule runs: it must parse (mostly) as Python, JavaScript or
TypeScript, contain real code constructs, and be more than a line or two.
"""

from __future__ import annotations

import ast
import re

from . import js_parser
from .source import SourceFile

MIN_CODE_LINES = 3
MAX_ERROR_RATIO = 0.25
SUPPORTED = "JavaScript, TypeScript (including React) and Python"
SUPPORTED_SHORT = "JavaScript, TypeScript or Python"

# Whole documents in another language. Checked first: HTML is also valid JSX.
_DOCUMENTS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("HTML", re.compile(r"\A\s*(<!DOCTYPE|<html[\s>])", re.I)),
    ("PHP", re.compile(r"<\?php")),
    ("a shell script", re.compile(r"\A#!\s*/(usr/)?bin/(env\s+)?(ba|z|da)?sh")),
)
# Unmistakable signatures of languages codegrade does not analyse.
_OTHER_LANGUAGES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "Java",
        re.compile(
            r"public\s+static\s+void\s+main|System\.out\.print|^[ \t]*package\s+[\w.]+;", re.M
        ),
    ),
    (
        "C#",
        re.compile(r"^[ \t]*using\s+System|Console\.Write(Line)?\(|^[ \t]*namespace\s+\w+", re.M),
    ),
    ("C or C++", re.compile(r"^[ \t]*#include\s*[<\"]|\bstd::|\bint\s+main\s*\(", re.M)),
    ("PHP", re.compile(r"^[ \t]*\$\w+\s*=.*;\s*$", re.M)),
    ("Go", re.compile(r"^[ \t]*package\s+main\b|^[ \t]*func\s+\w+\(.*\)\s*\{|\bfmt\.Print", re.M)),
    ("Rust", re.compile(r"\bfn\s+main\s*\(|\blet\s+mut\b|println!\(", re.M)),
    ("Ruby", re.compile(r"^[ \t]*end[ \t]*$|\bputs\s+['\"]", re.M)),
    (
        "SQL",
        re.compile(
            r"^[ \t]*(SELECT\s.+\sFROM|INSERT\s+INTO|CREATE\s+TABLE|UPDATE\s+\w+\s+SET)\b",
            re.I | re.M,
        ),
    ),
    ("CSS", re.compile(r"^[ \t]*[.#@:*\w][^{}\n]*\{\s*\n?\s*[\w-]+\s*:\s*[^;{}]+;", re.M)),
    ("a shell script", re.compile(r"^[ \t]*echo\s+[\"'$]", re.M)),
)  # fmt: skip
_MIN_PYTHON_HINTS = 2
_PYTHON_HINTS = re.compile(
    r"^[ \t]*(def \w+\(.*\).*:|class \w+.*:|from [\w.]+ import |import [\w.]+\s*$|elif .*:|"
    r"if __name__|print\()",
    re.M,
)
_PYTHON_STATEMENTS = (
    ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Import, ast.ImportFrom, ast.Assign,
    ast.AnnAssign, ast.AugAssign, ast.For, ast.While, ast.If, ast.With, ast.Try, ast.Return,
)  # fmt: skip
_JS_CONSTRUCTS = (
    "function_declaration", "arrow_function", "function_expression", "class_declaration",
    "lexical_declaration", "variable_declaration", "import_statement", "export_statement",
    "call_expression", "assignment_expression", "jsx_element", "jsx_self_closing_element",
    "interface_declaration", "type_alias_declaration",
)  # fmt: skip
_JSX = ("jsx_element", "jsx_self_closing_element")


class UngradableInputError(ValueError):
    """The input isn't code codegrade can grade. ``code`` says why, for clients to branch on."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code


def detect_extension(code: str) -> str:
    """File extension (".py", ".ts", ".tsx", ".js" or ".jsx") for pasted code.

    Raises :class:`UngradableInputError` for other languages, prose and random text.
    """
    for language, signature in _DOCUMENTS:
        if signature.search(code):
            raise _unsupported(language)
    if _parses_as_python(code):
        return ".py"
    dialect, module, ratio = _parse_javascript(code)
    has_code = module.has(*_JS_CONSTRUCTS)
    if not (ratio == 0 and has_code):
        # Only now look for other languages: an interface body looks like CSS, `$x = 1;` like
        # PHP, and neither should cost valid TypeScript its grade.
        _reject_other_languages(code)
        if len(_PYTHON_HINTS.findall(code)) >= _MIN_PYTHON_HINTS:
            return ".py"  # Python with a syntax error is still Python
        if ratio > MAX_ERROR_RATIO or not has_code:
            message = f"This doesn't look like source code. Paste {SUPPORTED}."
            raise UngradableInputError("not_code", message)
    is_typescript = dialect == "typescript" or module.has(*js_parser.TYPESCRIPT_ONLY_TYPES)
    base = ".ts" if is_typescript else ".js"
    return f"{base}x" if module.has(*_JSX) else base


def _reject_other_languages(code: str) -> None:
    for language, signature in _OTHER_LANGUAGES:
        if signature.search(code):
            raise _unsupported(language)


def _unsupported(language: str) -> UngradableInputError:
    message = f"This looks like {language}. CodeFlow grades {SUPPORTED}."
    return UngradableInputError("unsupported_language", message)


def _parses_as_python(code: str) -> bool:
    try:
        tree = ast.parse(code)
    except (SyntaxError, RecursionError, MemoryError, ValueError):
        return False
    nodes = list(ast.walk(tree))
    has_calls = any(isinstance(node, ast.Call) for node in nodes)
    return any(isinstance(node, _PYTHON_STATEMENTS) for node in nodes) or (
        has_calls and _PYTHON_HINTS.search(code) is not None
    )


def _parse_javascript(code: str) -> tuple[str, js_parser.JsModule, float]:
    """The dialect (TSX or TypeScript) that understands the most of ``code``."""
    size = len(code.encode("utf-8"))
    parsed = [(dialect, js_parser.parse(code, dialect)) for dialect in ("tsx", "typescript")]
    dialect, tree = min(parsed, key=lambda item: js_parser.error_ratio(item[1], size))
    module = js_parser.JsModule.build("snippet", "javascript", tree)
    return dialect, module, js_parser.error_ratio(tree, size)


def ensure_gradable(source: SourceFile) -> None:
    """Rejects a single submitted file that is too short or isn't really its claimed language."""
    if source.language == "python":
        if not _parses_as_python(source.raw):
            _reject_other_languages(source.raw)
            if len(_PYTHON_HINTS.findall(source.raw)) < _MIN_PYTHON_HINTS:
                raise _not_code(source.label)
    else:
        tree = source.tree
        ratio = js_parser.error_ratio(tree, len(source.raw.encode("utf-8")))
        if ratio > 0:  # Java and friends mostly parse as TypeScript; check before trusting it
            _reject_other_languages(source.raw)
        if ratio > 2 * MAX_ERROR_RATIO:
            raise _not_code(source.label)
    if source.code_lines < MIN_CODE_LINES:
        raise UngradableInputError(
            "too_little_code",
            f"There isn't enough code to grade: {source.code_lines} line(s) found, "
            f"at least {MIN_CODE_LINES} needed.",
        )


def _not_code(label: str) -> UngradableInputError:
    return UngradableInputError(
        "not_code", f"`{label}` doesn't look like {SUPPORTED_SHORT} source code."
    )
