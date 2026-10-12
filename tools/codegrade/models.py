"""Data model shared by the analyzers, scoring and reporting layers."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Severity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

    @property
    def penalty(self) -> int:
        """Points deducted from a file's score for one finding of this severity."""
        return {"error": 15, "warning": 7, "info": 3}[self.value]

    @property
    def rank(self) -> int:
        """Sort key: errors first."""
        return {"error": 0, "warning": 1, "info": 2}[self.value]


class Grade(str, Enum):
    """The final rank of a fully graded assignment (never of code quality alone)."""

    EXCELLENT = "Excellent"
    GOOD = "Good"
    POOR = "Poor"


class Dimension(str, Enum):
    """What a finding says about the code. Every rule belongs to exactly one dimension."""

    RELIABILITY = "reliability"
    COMPLEXITY = "complexity"
    READABILITY = "readability"
    DOCUMENTATION = "documentation"
    ACCESSIBILITY = "accessibility"
    TESTING = "testing"


_RULES_BY_DIMENSION: dict[Dimension, tuple[str, ...]] = {
    # Reliability: bugs, risky constructs, missing error handling, security.
    Dimension.RELIABILITY: (
        "syntax-error",
        "no-eval",
        "no-debugger",
        "sql-injection",
        "shell-injection",
        "hardcoded-secret",
        "dangerous-html",
        "eqeqeq",
        "no-var",
        "empty-catch",
        "bare-except",
        "swallowed-exception",
        "broad-except",
        "mutable-default",
        "no-global",
        "compare-to-none",
        "request-without-timeout",
        "unchecked-response",
        "unhandled-rejection",
        "unguarded-json-parse",
        "open-without-with",
        "unreachable-code",
        "unused-import",
        "unused-variable",
        "shadowed-builtin",
        "import-side-effects",
        "listener-cleanup",
        "effect-cleanup",
        "effect-race",
        "state-mutation",
        "index-as-key",
        "missing-key",
        "ts-suppression",
        "non-null-assertion",
    ),
    # Complexity: structure that makes code hard to change.
    Dimension.COMPLEXITY: (
        "function-length",
        "complexity",
        "deep-nesting",
        "file-length",
        "duplication",
        "nested-loops",
        "too-many-params",
    ),
    # Readability: what a reader has to decode.
    Dimension.READABILITY: (
        "short-names",
        "magic-numbers",
        "naming-convention",
        "nested-ternary",
        "commented-out-code",
        "no-console",
        "todo-comment",
        "lint-suppression",
        "range-len",
        "wildcard-import",
        "compare-to-bool",
    ),
    # Documentation and types: what tells the next developer how to use the code.
    Dimension.DOCUMENTATION: (
        "missing-docstrings",
        "missing-type-hints",
        "missing-docs",
        "no-types",
        "untyped-params",
        "no-explicit-any",
    ),
    # Accessibility: whether everyone can use the UI.
    Dimension.ACCESSIBILITY: (
        "img-alt",
        "button-type",
        "placeholder-href",
        "click-non-interactive",
        "input-label",
    ),
    # Testing: evidence that the code is verified.
    Dimension.TESTING: ("no-tests",),
}

RULE_DIMENSIONS: dict[str, Dimension] = {
    rule: dimension for dimension, rules in _RULES_BY_DIMENSION.items() for rule in rules
}


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: Severity
    message: str
    path: str
    line: int

    @property
    def dimension(self) -> Dimension:
        """The quality dimension this finding's rule belongs to."""
        return RULE_DIMENSIONS.get(self.rule, Dimension.RELIABILITY)


@dataclass(frozen=True)
class FunctionMetrics:
    name: str
    start_line: int
    end_line: int
    complexity: int
    max_nesting: int = 0
    params: int = 0

    @property
    def length(self) -> int:
        """Lines from the signature to the end of the body, inclusive."""
        return self.end_line - self.start_line + 1


@dataclass
class Structure:
    """What a language analyzer extracts from one file."""

    functions: list[FunctionMetrics] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    max_nesting: int = 0
    has_tests: bool = False


@dataclass
class FileReport:
    path: str
    language: str
    code_lines: int
    functions: list[FunctionMetrics] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    max_nesting: int = 0
    duplicated_lines: int = 0
    score: int = 100
    points_lost: dict[str, float] = field(default_factory=dict)

    @property
    def longest_function(self) -> int:
        """Length of the longest function in the file."""
        return max((function.length for function in self.functions), default=0)

    @property
    def max_complexity(self) -> int:
        """Highest cyclomatic complexity of any function in the file."""
        return max((function.complexity for function in self.functions), default=0)


@dataclass(frozen=True)
class HygieneCheck:
    name: str
    passed: bool
    weight: int
    hint: str


@dataclass
class ProjectReport:
    """Static code quality: per-file scores plus, for whole projects, hygiene."""

    root: str
    files: list[FileReport]
    hygiene: list[HygieneCheck]
    code_score: int
    hygiene_score: int | None
    quality_score: int
    points_lost: dict[str, float] = field(default_factory=dict)

    @property
    def findings(self) -> list[Finding]:
        """Every file's findings, most severe first."""
        every = [finding for report in self.files for finding in report.findings]
        return sorted(
            every, key=lambda finding: (finding.severity.rank, finding.path, finding.line)
        )
