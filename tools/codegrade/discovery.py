"""Finds the source files to analyse, skipping dependencies and build output."""

from __future__ import annotations

import fnmatch
import os
from collections.abc import Iterable, Iterator
from pathlib import Path

from .source import SUPPORTED_EXTENSIONS, display_path

EXCLUDED_DIRS = frozenset(
    {
        "node_modules",
        "dist",
        "build",
        "coverage",
        ".git",
        ".venv",
        "venv",
        "__pycache__",
        "__MACOSX",
        ".next",
        ".turbo",
        ".cache",
    }
)
DEFAULT_EXCLUDES = ("*.d.ts", "*.min.js")


def discover(paths: Iterable[Path], root: Path, excludes: Iterable[str] = ()) -> list[Path]:
    """Supported source files under ``paths``, minus default and user excludes."""
    patterns = (*DEFAULT_EXCLUDES, *excludes)
    found: set[Path] = set()
    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)
        candidates = [path] if path.is_file() else walk_files(path)
        found.update(
            candidate.resolve()
            for candidate in candidates
            if candidate.suffix.lower() in SUPPORTED_EXTENSIONS
            and not _is_excluded(display_path(candidate, root), patterns)
        )
    return sorted(found)


def walk_files(directory: Path) -> Iterator[Path]:
    """Every file under ``directory``, skipping dependency and build directories."""
    for current, dirs, files in os.walk(directory):
        dirs[:] = sorted(name for name in dirs if name not in EXCLUDED_DIRS)
        for name in sorted(files):
            yield Path(current, name)


def is_excluded_path(label: str) -> bool:
    """True for paths inside dependency/build directories or matching the default excludes."""
    parts = label.split("/")
    return any(part in EXCLUDED_DIRS for part in parts[:-1]) or _is_excluded(
        label, DEFAULT_EXCLUDES
    )


def _is_excluded(label: str, patterns: Iterable[str]) -> bool:
    name = label.rsplit("/", 1)[-1]
    return any(
        fnmatch.fnmatch(label, pattern) or fnmatch.fnmatch(name, pattern) for pattern in patterns
    )
