"""Orchestrates analysis: sources → structure → findings → scored reports."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from .assignment import (
    Assignment,
    Reviewer,
    StaticCheck,
    SubmissionReport,
    grade_submission,
    run_review,
)
from .duplication import find_duplicate_lines
from .hygiene import ProjectSnapshot, check_hygiene, hygiene_score, snapshot_directory
from .js_analyzer import analyze_js, syntax_findings
from .js_parser import JsModule, error_ratio, max_depth
from .js_rules import JS_RULES
from .js_style import STYLE_RULES
from .jsx_rules import JSX_RULES
from .languages import detect_extension, ensure_gradable
from .models import FileReport, Finding, ProjectReport, Severity, Structure
from .py_analyzer import analyze_python
from .scoring import (
    DEFAULT_THRESHOLDS,
    Thresholds,
    metric_findings,
    missing_tests_finding,
    points_lost,
    quality_score,
    score_findings,
    weighted_code_score,
    weighted_points_lost,
)
from .source import SUPPORTED_EXTENSIONS, SourceFile, is_test_file
from .task_signals import static_checks


def load_sources(paths: Sequence[Path], root: Path) -> list[SourceFile]:
    """Reads every supported file, labelled relative to ``root``."""
    return [source for path in paths if (source := SourceFile.load(path, root)) is not None]


def analyze_project(
    paths: Sequence[Path],
    root: Path,
    *,
    include_hygiene: bool = True,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
) -> ProjectReport:
    """Static quality of files on disk; hygiene is checked against the directory at ``root``."""
    snapshot = snapshot_directory(root) if include_hygiene else None
    return build_report(
        load_sources(paths, root), snapshot, root_label=str(root), thresholds=thresholds
    )


def review_submission(
    sources: Sequence[SourceFile],
    snapshot: ProjectSnapshot | None,
    *,
    root_label: str,
    assignment: Assignment,
    reviewer: Reviewer | None,
) -> SubmissionReport:
    """Static quality, static task checks and, when a reviewer is available, the AI review."""
    quality = build_report(sources, snapshot, root_label=root_label)
    outcome = run_review(reviewer, assignment, sources)
    return grade_submission(quality, outcome, static_checks(assignment, sources))


def build_report(
    sources: Sequence[SourceFile],
    snapshot: ProjectSnapshot | None,
    *,
    root_label: str,
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
) -> ProjectReport:
    """Scores in-memory sources.

    With a ``snapshot`` the project's hygiene (README, tests, CI…) is part of the score.
    Without one the sources are graded as a standalone submission, which is expected to bring
    its own tests.
    """
    files = analyze_sources(sources, thresholds, standalone=snapshot is None)
    code_score = weighted_code_score(files)
    hygiene = check_hygiene(snapshot) if snapshot is not None else []
    project_hygiene = hygiene_score(hygiene) if snapshot is not None else None
    return ProjectReport(
        root=root_label,
        files=files,
        hygiene=hygiene,
        code_score=code_score,
        hygiene_score=project_hygiene,
        quality_score=quality_score(code_score, project_hygiene),
        points_lost=weighted_points_lost(files),
    )


def analyze_sources(
    sources: Sequence[SourceFile],
    thresholds: Thresholds = DEFAULT_THRESHOLDS,
    *,
    standalone: bool = False,
) -> list[FileReport]:
    """Per-file reports, with duplication and test coverage judged across all of the sources."""
    duplicates = find_duplicate_lines(sources)
    structures = [(source, structure_of(source)) for source in sources]
    tested = any(is_test_file(source.label) or found.has_tests for source, found in structures)
    reports = []
    for source, structure in structures:
        if standalone and not tested:
            structure.findings.append(missing_tests_finding(source.label))
        reports.append(
            _file_report(source, structure, duplicates.get(source.label, []), thresholds)
        )
    return reports


MAX_SYNTAX_DEPTH = 300  # real code stays far below this; hostile input doesn't
MAX_ERROR_RATIO = 0.5  # beyond this the "tree" is a heap of error nodes, not code to analyse


def structure_of(source: SourceFile) -> Structure:
    """Function metrics and rule findings for one file, whatever its language."""
    if source.language == "python":
        return analyze_python(source)
    tree = source.tree
    if error_ratio(tree, len(source.raw.encode("utf-8"))) > MAX_ERROR_RATIO:
        # Rules need a sensible tree. Report what is wrong and score the file as broken.
        module = JsModule.build(source.label, source.language, tree)
        return Structure(findings=syntax_findings(module))
    if max_depth(tree) > MAX_SYNTAX_DEPTH:
        message = f"syntax nested over {MAX_SYNTAX_DEPTH} levels deep; too tangled to analyse"
        return Structure(
            findings=[Finding("deep-nesting", Severity.ERROR, message, source.label, 1)]
        )
    module = JsModule.build(source.label, source.language, source.tree)
    structure = analyze_js(module)
    # Style rules judge production code; tests are allowed magic numbers and short names.
    rules = (*JS_RULES, *JSX_RULES, *(() if is_test_file(source.label) else STYLE_RULES))
    for rule in rules:
        structure.findings.extend(rule(module))
    return structure


def _file_report(
    source: SourceFile, structure: Structure, duplicate_lines: list[int], thresholds: Thresholds
) -> FileReport:
    report = FileReport(
        path=source.label,
        language=source.language,
        code_lines=source.code_lines,
        functions=structure.functions,
        findings=structure.findings,
        max_nesting=structure.max_nesting,
        duplicated_lines=len(duplicate_lines),
    )
    report.findings.extend(metric_findings(report, duplicate_lines, thresholds))
    report.findings.sort(key=lambda finding: (finding.severity.rank, finding.line))
    report.score = score_findings(report.findings)
    report.points_lost = points_lost(report.findings, report.score)
    return report


def analyze_snippet(
    code: str, assignment: Assignment, *, filename: str | None = None, extension: str | None = None
) -> tuple[str, ProjectReport, tuple[StaticCheck, ...]]:
    """Gate, quality and static task checks for pasted code, as one unit of work.

    The unit is picklable on purpose: the API runs it in a worker process it can kill.
    ``filename`` wins when it has a supported extension, then ``extension``, then detection.
    Raises :class:`~tools.codegrade.languages.UngradableInputError` for anything that isn't
    gradable code. Returns the file name used, its report and the static checks.
    """
    label = _snippet_label(code, filename, extension)
    source = SourceFile.from_text(label, code)
    if source is None:  # _snippet_label only returns supported names
        raise ValueError(f"unsupported file type: {label}")
    ensure_gradable(source)
    report = build_report([source], None, root_label=label)
    return label, report, static_checks(assignment, [source])


def analyze_submission(
    sources: Sequence[SourceFile],
    snapshot: ProjectSnapshot | None,
    root_label: str,
    assignment: Assignment,
) -> tuple[ProjectReport, tuple[StaticCheck, ...]]:
    """Quality and static task checks for a whole project (the archive counterpart)."""
    report = build_report(sources, snapshot, root_label=root_label)
    return report, static_checks(assignment, sources)


def _snippet_label(code: str, filename: str | None, extension: str | None) -> str:
    name = (filename or "").strip().replace("\\", "/").rsplit("/", 1)[-1]
    if name and any(name.lower().endswith(suffix) for suffix in SUPPORTED_EXTENSIONS):
        return name
    return f"snippet{extension or detect_extension(code)}"
