"""Command-line entry point: ``python3 -m tools.codegrade [paths...]``."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from . import __version__
from .ai_review import reviewer_from_env
from .analyzer import build_report, load_sources
from .archive import ArchiveError, read_archive
from .assignment import (
    Assignment,
    ReviewOutcome,
    ReviewStatus,
    SubmissionReport,
    grade_submission,
    run_review,
)
from .discovery import discover
from .hygiene import ProjectSnapshot, snapshot_directory
from .report import render_json
from .source import SourceFile
from .task_signals import static_checks
from .text_report import render_text

EXIT_OK, EXIT_BELOW_THRESHOLD, EXIT_USAGE = 0, 1, 2


class UsageError(Exception):
    """Bad arguments or unreadable input; the message is printed for the user."""


@dataclass(frozen=True)
class Submission:
    sources: list[SourceFile]
    snapshot: ProjectSnapshot | None
    label: str
    source: str  # "archive" or "files"


def build_parser() -> argparse.ArgumentParser:
    """The argument parser (exposed for documentation and tests)."""
    parser = argparse.ArgumentParser(
        prog="codegrade",
        description=(
            "Score code quality from 0 to 100. With --task and --explanation, an AI review also "
            "checks whether the code solves the task (50%%), alongside code quality (35%%) and "
            "the explanation (15%%), and the submission is ranked Excellent, Good or Poor."
        ),
        epilog="Exit codes: 0 = ok, 1 = score below --fail-under, 2 = usage error.",
    )
    parser.add_argument(
        "paths", nargs="*", default=["."], help="files, directories or one .zip (default: .)"
    )
    parser.add_argument("--root", default=".", help="project root for hygiene checks (default: .)")
    parser.add_argument(
        "--exclude", action="append", default=[], metavar="GLOB", help="skip matching files"
    )
    parser.add_argument("--task", help="the assignment text")
    parser.add_argument("--task-file", type=Path, help="read the assignment from a file")
    parser.add_argument("--explanation", help="how the solution works, in the author's words")
    parser.add_argument("--explanation-file", type=Path, help="read the explanation from a file")
    parser.add_argument("--format", choices=("text", "json"), default="text", help="output format")
    parser.add_argument(
        "--fail-under", type=int, metavar="SCORE", help="exit 1 if the score is below SCORE"
    )
    parser.add_argument(
        "--no-hygiene", action="store_true", help="grade code only, skip project checks"
    )
    parser.add_argument("--no-color", action="store_true", help="disable ANSI colours")
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="list every finding, info included"
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Runs the CLI and returns its exit code."""
    args = build_parser().parse_args(argv)
    try:
        submission = _load_submission(args)
        report = _grade(submission, args)
    except (UsageError, ArchiveError) as error:
        print(f"codegrade: {error}", file=sys.stderr)
        return EXIT_USAGE

    if args.format == "json":
        print(render_json(report, source=submission.source))
    else:
        print(render_text(report, color=_use_color(args.no_color), verbose=args.verbose))

    if args.fail_under is not None and report.gate_score < args.fail_under:
        score, minimum = report.gate_score, args.fail_under
        print(f"codegrade: score {score} is below --fail-under {minimum}", file=sys.stderr)
        return EXIT_BELOW_THRESHOLD
    return EXIT_OK


def _load_submission(args: argparse.Namespace) -> Submission:
    """A single .zip archive, or files and directories on disk."""
    if len(args.paths) == 1 and args.paths[0].lower().endswith(".zip"):
        archive_path = Path(args.paths[0])
        if not archive_path.is_file():
            raise UsageError(f"path not found: {archive_path}")
        contents = read_archive(archive_path.read_bytes())
        snapshot = None if args.no_hygiene else contents.snapshot
        return Submission(contents.sources, snapshot, archive_path.name, "archive")

    root = Path(args.root).resolve()
    try:
        files = discover([Path(path) for path in args.paths], root, args.exclude)
    except FileNotFoundError as error:
        raise UsageError(f"path not found: {error}") from error
    if not files:
        raise UsageError("no supported source files found")
    snapshot = None if args.no_hygiene else snapshot_directory(root)
    return Submission(load_sources(files, root), snapshot, str(root), "files")


def _grade(submission: Submission, args: argparse.Namespace) -> SubmissionReport:
    quality = build_report(submission.sources, submission.snapshot, root_label=submission.label)
    task = _text_argument(args.task, args.task_file, "--task")
    explanation = _text_argument(args.explanation, args.explanation_file, "--explanation")
    if task is None and explanation is None:
        return grade_submission(quality, ReviewOutcome(ReviewStatus.NOT_REQUESTED))
    if not task or not explanation:
        raise UsageError("an AI review needs both --task and --explanation")
    assignment = Assignment(task, explanation)
    outcome = run_review(reviewer_from_env(), assignment, submission.sources)
    return grade_submission(quality, outcome, static_checks(assignment, submission.sources))


def _text_argument(text: str | None, path: Path | None, flag: str) -> str | None:
    if text is not None and path is not None:
        raise UsageError(f"use either {flag} or {flag}-file, not both")
    if path is None:
        return text
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise UsageError(f"cannot read {path}: {error.strerror}") from error


def _use_color(disabled: bool) -> bool:
    return not disabled and "NO_COLOR" not in os.environ and sys.stdout.isatty()
