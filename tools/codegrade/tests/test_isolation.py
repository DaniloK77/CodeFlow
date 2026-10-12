"""Killable analysis: pathological input costs the caller a timeout, never a stuck thread."""

from __future__ import annotations

import os
import time

import pytest

from tools.codegrade.analyzer import build_report
from tools.codegrade.isolation import AnalysisCrashedError, AnalysisTimeoutError, run_isolated
from tools.codegrade.languages import UngradableInputError, detect_extension
from tools.codegrade.source import SourceFile

CLEAN = "export const double = (value: number): number => value * 2;\n"
UNCLOSED_QUOTES = '"' * 300_000  # tree-sitter's error recovery goes quadratic on this


def quality_of(code: str, label: str) -> int:
    source = SourceFile.from_text(label, code)
    assert source is not None
    return build_report([source], None, root_label=label).quality_score


def reject(code: str) -> str:
    return detect_extension(code)


def crash() -> None:
    raise RuntimeError("boom")


def die() -> None:
    os._exit(1)


def sleep_forever() -> None:
    time.sleep(60)


def test_returns_what_the_function_returns() -> None:
    assert run_isolated(quality_of, CLEAN, "double.ts", timeout=20) == quality_of(CLEAN, "a.ts")


def test_input_that_is_not_code_is_still_a_rejection() -> None:
    with pytest.raises(UngradableInputError) as rejection:
        run_isolated(reject, "just some words, nothing else", timeout=20)
    assert rejection.value.code == "not_code"


def test_a_worker_that_overruns_is_killed() -> None:
    started = time.perf_counter()
    with pytest.raises(AnalysisTimeoutError):
        run_isolated(sleep_forever, timeout=0.5)
    assert time.perf_counter() - started < 5


def test_pathological_input_times_out_instead_of_hanging() -> None:
    started = time.perf_counter()
    with pytest.raises(AnalysisTimeoutError):
        run_isolated(quality_of, UNCLOSED_QUOTES, "evil.ts", timeout=1.5)
    assert time.perf_counter() - started < 6


def test_an_unexpected_error_is_reported_not_raised_as_is() -> None:
    with pytest.raises(AnalysisCrashedError, match="boom"):
        run_isolated(crash, timeout=20)


def test_a_worker_that_dies_is_reported() -> None:
    with pytest.raises(AnalysisCrashedError, match="without an answer"):
        run_isolated(die, timeout=20)
