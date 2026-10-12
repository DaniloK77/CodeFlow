"""Builders shared by the codegrade test suite."""

from __future__ import annotations

import textwrap
from collections.abc import Iterable

from tools.codegrade.analyzer import structure_of
from tools.codegrade.models import Finding, Structure
from tools.codegrade.source import SourceFile


def make_source(code: str, name: str = "sample.tsx") -> SourceFile:
    """A source file from an indented triple-quoted string."""
    source = SourceFile.from_text(name, textwrap.dedent(code).lstrip("\n"))
    assert source is not None, f"unsupported test file name: {name}"
    return source


def analyze(code: str, name: str = "sample.tsx") -> Structure:
    """Metrics and rule findings for ``code``, as the analyzer produces them."""
    return structure_of(make_source(code, name))


def rules_of(findings: Iterable[Finding]) -> list[str]:
    """Sorted rule names, duplicates kept."""
    return sorted(finding.rule for finding in findings)


def rules_in(code: str, name: str = "sample.tsx") -> list[str]:
    """Sorted names of the rules ``code`` breaks."""
    return rules_of(analyze(code, name).findings)
