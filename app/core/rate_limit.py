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
        # calculate time until the next hit is allowed
        reset = self._strategy.get_window_stats(item, scope, key).reset_time
        return TooManyRequestsError(
            headers={"Retry-After": str(max(1, int(reset - time.time())))}
        )

    def check(self, scope: str, key: str, rule: str) -> None:
        # count one hit and refuse once the rule is used up
        item = parse(rule)
        if not self._strategy.hit(item, scope, key):
            raise self._retry_after(item, scope, key)

    def ensure_allowed(self, scope: str, key: str, rule: str) -> None:
        # check if the rule is still allowed without counting a hit
        item = parse(rule)
        if not self._strategy.test(item, scope, key):
            raise self._retry_after(item, scope, key)

    def record(self, scope: str, key: str, rule: str) -> None:
        # record a hit for the given rule
        self._strategy.hit(parse(rule), scope, key)

    def clear(self, scope: str, key: str, rule: str) -> None:
        # clear all hits for the given rule
        self._strategy.clear(parse(rule), scope, key)
