"""Runs engine work in killable worker processes, a few at a time."""

from __future__ import annotations

import threading
from collections.abc import Callable
from typing import ParamSpec, TypeVar

from tools.codegrade.isolation import run_isolated

P = ParamSpec("P")
R = TypeVar("R")


class ServiceBusyError(Exception):
    """Every analysis slot stayed taken for as long as a request is willing to wait."""


class AnalysisRunner:
    """Analyses untrusted code with a time limit, never more than ``slots`` at once.

    Each analysis is a separate process (see :mod:`tools.codegrade.isolation`), so a request
    that sends pathological code costs one worker for ``timeout`` seconds and nothing more.
    """

    def __init__(self, timeout: float, slots: int) -> None:
        self.timeout = timeout
        self._slots = threading.BoundedSemaphore(slots)

    def run(self, function: Callable[P, R], *args: P.args, **kwargs: P.kwargs) -> R:
        """``function(*args, **kwargs)`` in a worker; raises the errors of ``run_isolated``."""
        if not self._slots.acquire(timeout=self.timeout):
            raise ServiceBusyError("The grader is busy right now. Please try again in a moment.")
        try:
            return run_isolated(function, *args, timeout=self.timeout, **kwargs)
        finally:
            self._slots.release()
