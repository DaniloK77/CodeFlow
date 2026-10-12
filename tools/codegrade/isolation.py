"""Runs an analysis in a child process that can be killed.

tree-sitter's error recovery is not linear on every malformed input (40 KB of unclosed quotes
takes seconds, and a C call can't be interrupted from Python), so a server that grades
untrusted uploads can't just call the parser from a request thread. The work runs in a
short-lived worker instead: if it doesn't answer within ``timeout`` it is killed and the
caller gets :class:`AnalysisTimeoutError`.

The worker is started with ``forkserver`` (``spawn`` on Windows), so it never inherits the
server's threads or locks.
Arguments and results travel by pickle, so they must be plain data (no parsed trees).
"""

from __future__ import annotations

import multiprocessing
import traceback
from collections.abc import Callable
from multiprocessing.connection import Connection
from typing import Any, ParamSpec, TypeVar

from .languages import UngradableInputError

P = ParamSpec("P")
R = TypeVar("R")
DEFAULT_TIMEOUT_SECONDS = 10.0
# forkserver where it exists (Linux, macOS); spawn elsewhere (Windows). Both start from a clean
# interpreter, so a worker never inherits the server's threads or locks.
_METHOD = "forkserver" if "forkserver" in multiprocessing.get_all_start_methods() else "spawn"
_CONTEXT = multiprocessing.get_context(_METHOD)
if _METHOD == "forkserver":
    _CONTEXT.set_forkserver_preload(["tools.codegrade.analyzer"])


class AnalysisTimeoutError(Exception):
    """The analysis didn't finish in time, which is what pathological input looks like."""


class AnalysisCrashedError(Exception):
    """The worker died or failed unexpectedly. The message carries what is known."""


def run_isolated(
    function: Callable[P, R],
    *args: P.args,
    timeout: float = DEFAULT_TIMEOUT_SECONDS,
    **kwargs: P.kwargs,
) -> R:
    """Calls ``function(*args, **kwargs)`` in a worker process and returns its result.

    :class:`UngradableInputError` is re-raised as is. A worker that exceeds ``timeout`` is
    killed (:class:`AnalysisTimeoutError`); any other failure becomes
    :class:`AnalysisCrashedError`.
    """
    receiver, sender = _CONTEXT.Pipe(duplex=False)
    worker = _CONTEXT.Process(target=_work, args=(sender, function, args, kwargs), daemon=True)
    worker.start()
    sender.close()  # only the worker writes; this lets recv() see a dead worker as EOF
    try:
        if not receiver.poll(timeout):
            raise AnalysisTimeoutError(f"analysis took longer than {timeout:g} s")
        outcome = _receive(receiver)
    finally:
        receiver.close()
        if worker.is_alive():
            worker.kill()
        worker.join()

    kind, *payload = outcome
    if kind == "ok":
        return payload[0]
    if kind == "rejected":
        raise UngradableInputError(*payload)
    raise AnalysisCrashedError(payload[0])


def _receive(receiver: Connection) -> tuple[Any, ...]:
    try:
        return receiver.recv()
    except EOFError:
        return ("crashed", "the analysis worker exited without an answer")


def _work(
    sender: Connection, function: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]
) -> None:
    try:
        message: tuple[Any, ...] = ("ok", function(*args, **kwargs))
    except UngradableInputError as error:
        message = ("rejected", error.code, str(error))
    except Exception:
        message = ("crashed", traceback.format_exc(limit=5))
    try:
        sender.send(message)  # an unpicklable result ends the worker, which the parent sees as EOF
    finally:
        sender.close()
