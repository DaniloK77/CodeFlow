"""Daily allowance of AI reviews, per visitor and for the service as a whole.

Static analysis is free and unlimited (subject to the request rate limit); AI reviews cost
money, so they are counted. Counters live in process memory: right for a single instance,
and the place to plug in Redis when the API runs on several.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

DAY_SECONDS = 24 * 60 * 60
_EVERYONE = "*"


class DailyQuota:
    def __init__(
        self,
        per_client: int,
        overall: int,
        window_seconds: float = DAY_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.per_client = per_client
        self.overall = overall
        self.window = window_seconds
        self._clock = clock
        self._uses: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def acquire(self, client: str) -> float | None:
        """Takes one review. Returns None if allowed, else seconds until one frees up."""
        now = self._clock()
        with self._lock:
            mine, everyone = self._recent(client, now), self._recent(_EVERYONE, now)
            for uses, limit in ((mine, self.per_client), (everyone, self.overall)):
                if len(uses) >= limit:
                    return uses[0] + self.window - now
            mine.append(now)
            everyone.append(now)
            return None

    def release(self, client: str) -> None:
        """Gives back the most recent review (it failed, so it shouldn't count)."""
        with self._lock:
            for key in (client, _EVERYONE):
                if self._uses[key]:
                    self._uses[key].pop()

    def remaining(self, client: str) -> int:
        """Reviews this client can still start right now."""
        now = self._clock()
        with self._lock:
            mine = len(self._recent(client, now))
            everyone = len(self._recent(_EVERYONE, now))
        return max(0, min(self.per_client - mine, self.overall - everyone))

    def _recent(self, key: str, now: float) -> deque[float]:
        uses = self._uses[key]
        while uses and uses[0] <= now - self.window:
            uses.popleft()
        return uses
