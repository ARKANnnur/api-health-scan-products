"""In-memory rate limiter sederhana.

NOTE: Hanya bekerja untuk single-instance deployment.
Kalau scale ke multi-instance, migrasi ke Redis/Upstash.
"""

import asyncio
import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def is_allowed(self, key: str) -> bool:
        """Return True kalau request boleh lanjut."""
        now = time.time()
        cutoff = now - self.window_seconds

        async with self._lock:
            timestamps = self._buckets[key]
            # Buang timestamp yang udah expired
            self._buckets[key] = [t for t in timestamps if t > cutoff]

            if len(self._buckets[key]) >= self.max_requests:
                return False

            self._buckets[key].append(now)
            return True


# Singleton instances
signup_limiter = RateLimiter(max_requests=5, window_seconds=3600)  # 5/jam
signin_ip_limiter = RateLimiter(max_requests=10, window_seconds=900)  # 10/15min
signin_email_limiter = RateLimiter(max_requests=5, window_seconds=900)  # 5/15min
