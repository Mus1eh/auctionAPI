import time

from limits import parse
from limits.storage import storage_from_string
from limits.strategies import MovingWindowRateLimiter

from app.core.exceptions import TooManyRequestsError


class RateLimiter:
    def __init__(self, storage_url: str):
        self._storage = storage_from_string(storage_url)
        self._strategy = MovingWindowRateLimiter(self._storage)

    def _retry_after(self, item, scope, key) -> TooManyRequestsError:
        reset = self._strategy.get_window_stats(item, scope, key).reset_time
        return TooManyRequestsError(
            headers={"Retry-After": str(max(1, int(reset - time.time())))}
        )

    def check(self, scope: str, key: str, rule: str) -> None:
        """Count one hit, and refuse once the rule is used up."""
        item = parse(rule)
        if not self._strategy.hit(item, scope, key):
            raise self._retry_after(item, scope, key)

    def ensure_allowed(self, scope: str, key: str, rule: str) -> None:
        """Refuse if the rule is already used up, without counting anything.

        For rules that only count failures: call this first, then record() a failure.
        """
        item = parse(rule)
        if not self._strategy.test(item, scope, key):
            raise self._retry_after(item, scope, key)

    def record(self, scope: str, key: str, rule: str) -> None:
        self._strategy.hit(parse(rule), scope, key)

    def clear(self, scope: str, key: str, rule: str) -> None:
        self._strategy.clear(parse(rule), scope, key)
