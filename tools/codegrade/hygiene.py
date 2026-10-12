"""Project-level engineering hygiene: the things a reviewer checks before reading code.

Checks run against a ``ProjectSnapshot`` (a file listing plus the README text), so the
same rules work for a directory on disk and for an uploaded .zip archive.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .discovery import walk_files
from .models import HygieneCheck
from .source import display_path, is_test_file

_README_BOILERPLATE = (
    "This template provides a minimal setup to get React working in Vite",
    "Getting Started with Create React App",
)
MIN_README_LINES = 30


@dataclass(frozen=True)
class ProjectSnapshot:
    """Relative POSIX paths of a project's files, plus the root README's text."""

    paths: frozenset[str]
    readme: str | None = None

    def has(self, *patterns: str) -> bool:
        return any(
            fnmatch.fnmatchcase(path, pattern) for path in self.paths for pattern in patterns
        )


def snapshot_directory(root: Path) -> ProjectSnapshot:
    """File listing and README of a project on disk."""
    paths = frozenset(display_path(path, root) for path in walk_files(root))
    readme_path = root / "README.md"
    readme = (
        readme_path.read_text(encoding="utf-8", errors="replace") if readme_path.is_file() else None
    )
    return ProjectSnapshot(paths, readme)


def _any_of(*patterns: str) -> Callable[[ProjectSnapshot], bool]:
    return lambda snapshot: snapshot.has(*patterns)


def _has_real_readme(snapshot: ProjectSnapshot) -> bool:
    if snapshot.readme is None:
        return False
    substantial = (
        sum(1 for line in snapshot.readme.splitlines() if line.strip()) >= MIN_README_LINES
    )
    return substantial and not any(marker in snapshot.readme for marker in _README_BOILERPLATE)


def _has_tests(snapshot: ProjectSnapshot) -> bool:
    return any(is_test_file(path) for path in snapshot.paths)


@dataclass(frozen=True)
class _Rule:
    name: str
    weight: int
    hint: str
    passes: Callable[[ProjectSnapshot], bool]


# Weights sum to 100, so the hygiene score reads as a percentage.
RULES: tuple[_Rule, ...] = (
    _Rule("README", 15, "document setup, scripts and architecture in README.md", _has_real_readme),
    _Rule("Automated tests", 20, "add unit tests (*.test.tsx, test_*.py)", _has_tests),
    _Rule(
        "Continuous integration",
        15,
        "run checks on every push (.github/workflows)",
        _any_of(".github/workflows/*.yml", ".github/workflows/*.yaml", ".gitlab-ci.yml"),
    ),
    _Rule(
        "Linter",
        10,
        "configure ESLint / Ruff",
        _any_of("eslint.config.*", ".eslintrc*", "ruff.toml", ".ruff.toml", ".flake8"),
    ),
    _Rule(
        "Formatter",
        10,
        "configure Prettier / Black",
        _any_of(".prettierrc*", "prettier.config.*", "pyproject.toml"),
    ),
    _Rule(
        "Static typing",
        10,
        "add TypeScript (tsconfig.json) or mypy",
        _any_of("tsconfig.json", "mypy.ini", "pyrightconfig.json"),
    ),
    _Rule("License", 5, "add a LICENSE file", _any_of("LICENSE*", "LICENCE*")),
    _Rule(".gitignore", 5, "ignore build output and dependencies", _any_of(".gitignore")),
    _Rule(
        "Lockfile",
        5,
        "commit a dependency lockfile",
        _any_of("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock", "uv.lock"),
    ),
    _Rule(
        "EditorConfig", 5, "add .editorconfig for consistent whitespace", _any_of(".editorconfig")
    ),
)


def check_hygiene(snapshot: ProjectSnapshot) -> list[HygieneCheck]:
    return [
        HygieneCheck(rule.name, rule.passes(snapshot), rule.weight, rule.hint) for rule in RULES
    ]


def hygiene_score(checks: list[HygieneCheck]) -> int:
    return sum(check.weight for check in checks if check.passed)
