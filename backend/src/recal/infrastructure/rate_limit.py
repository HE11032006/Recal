from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from time import monotonic


@dataclass(slots=True)
class RateLimitDecision:
    allowed: bool
    retry_after_seconds: int = 0


class InMemoryRateLimiter:
    """Rate limiter local pour le développement et une instance unique.

    En production multi-instance, remplacer le stockage mémoire par Redis ou
    DynamoDB afin que la limite soit partagée entre toutes les instances.
    """

    def __init__(self, *, max_requests: int = 5, window_seconds: int = 60) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> RateLimitDecision:
        now = monotonic()
        timestamps = self._requests[key]
        cutoff = now - self.window_seconds
        while timestamps and timestamps[0] <= cutoff:
            timestamps.popleft()
        if len(timestamps) >= self.max_requests:
            retry_after = max(1, int(timestamps[0] + self.window_seconds - now))
            return RateLimitDecision(False, retry_after)
        timestamps.append(now)
        return RateLimitDecision(True)
