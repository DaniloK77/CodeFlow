"""Policy shared by the Python and JavaScript rules: naming, numbers, secrets, aggregation."""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence

from .models import Finding, Severity

# Conventional one-letter names: loop indices, counts, coordinates, exceptions/events, "unused".
ALLOWED_SHORT_NAMES = frozenset({"_", "i", "j", "k", "n", "x", "y", "e"})
MAGIC_NUMBER_WARNING = 4  # one stray number is a note; a habit is a warning
LISTED_NAMES = 4
MIN_SECRET_LENGTH = 8
SECRET_NAME = re.compile(r"(?i)(api[_-]?key|secret|passw(or)?d|token|private[_-]?key)")
_PLACEHOLDER_SECRET = re.compile(r"(?i)^(x+|\*+|changeme|your[-_ ].*|<.*>|example.*|test.*|)$")


def aggregate_severity(count: int) -> Severity:
    """One occurrence is a note; a habit (two or more) is a warning."""
    return Severity.WARNING if count >= 2 else Severity.INFO


def listed(names: Iterable[str]) -> str:
    """Up to four names in backticks, e.g. "`a`, `b`" (with "…" when there are more)."""
    unique = list(dict.fromkeys(names))
    shown = ", ".join(f"`{name}`" for name in unique[:LISTED_NAMES])
    return f"{shown}, …" if len(unique) > LISTED_NAMES else shown


def is_secret_value(value: str) -> bool:
    """A string long enough to be a real credential and not an obvious placeholder."""
    return len(value) >= MIN_SECRET_LENGTH and not _PLACEHOLDER_SECRET.match(value)


def short_names_finding(names: Mapping[str, int], label: str) -> Finding | None:
    """One finding listing every single-letter name; ``names`` maps name → first line."""
    if not names:
        return None
    message = f"single-letter names ({listed(sorted(names))}) don't say what they hold"
    severity = aggregate_severity(len(names))
    return Finding("short-names", severity, message, label, min(names.values()))


def magic_numbers_finding(found: Sequence[tuple[int, str]], label: str) -> Finding | None:
    """One finding for unexplained numeric literals; ``found`` holds (line, literal) pairs."""
    if not found:
        return None
    severity = Severity.WARNING if len(found) >= MAGIC_NUMBER_WARNING else Severity.INFO
    values = ", ".join(dict.fromkeys(value for _, value in sorted(found)))
    message = f"{len(found)} unexplained number(s) ({values}); name them as constants"
    return Finding("magic-numbers", severity, message, label, min(line for line, _ in found))
