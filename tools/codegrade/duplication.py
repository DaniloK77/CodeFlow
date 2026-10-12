"""Copy-paste detection: substantial code lines that appear more than once in the project."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

from .source import SourceFile, is_test_file

MIN_LINE_LENGTH = 30
_IGNORED_PREFIXES = ("import ", "export {", "export *", "from ", "} from ")


def significant_lines(source: SourceFile) -> list[tuple[int, str]]:
    """(line number, whitespace-normalised text) for code lines long enough to be meaningful."""
    lines: list[tuple[int, str]] = []
    for number in sorted(source.code_line_numbers):
        if number > len(source.lines):
            continue
        text = " ".join(source.lines[number - 1].split())
        if len(text) >= MIN_LINE_LENGTH and not text.startswith(_IGNORED_PREFIXES):
            lines.append((number, text))
    return lines


def find_duplicate_lines(sources: Iterable[SourceFile]) -> dict[str, list[int]]:
    """Line numbers, per file, of every repeat after a line's first occurrence.

    Test files are skipped: repeated arrange/assert lines keep tests readable on purpose.
    """
    seen: set[str] = set()
    duplicates: dict[str, list[int]] = defaultdict(list)
    production = (source for source in sources if not is_test_file(source.label))
    for source in sorted(production, key=lambda item: item.label):
        for number, text in significant_lines(source):
            if text in seen:
                duplicates[source.label].append(number)
            else:
                seen.add(text)
    return dict(duplicates)
