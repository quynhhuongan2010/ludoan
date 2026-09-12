"""
Module quan ly Rate Limiting va Chong do quet mat khau (Brute-force Protection).
Chay 100% in-memory thread-safe, phu hop mang noi bo quan su khong co internet.
"""

import time
import threading
from typing import Optional, Tuple
from app.core.config import settings


class LoginBruteForceProtector:
    """Theo doi va ngan chan tan cong brute-force dang nhap."""

    def __init__(
        self,
        max_failures: int = 5,
        failure_window_seconds: int = 300,  # 5 phut
        lockout_duration_seconds: int = 900,  # 15 phut
    ):
        self.max_failures = max_failures
        self.failure_window = failure_window_seconds
        self.lockout_duration = lockout_duration_seconds
        self._lock = threading.Lock()
        # key -> list of float timestamps
        self._failures: dict[str, list[float]] = {}
        # key -> float timestamp expiration
        self._lockouts: dict[str, float] = {}
        self._last_cleanup = time.time()

    def _keys_for(self, ip: Optional[str], username: str) -> list[str]:
        keys = []
        u = username.strip().lower()
        if u:
            keys.append(f"user:{u}")
        if ip and ip.strip():
            keys.append(f"ip:{ip.strip()}")
        return keys

    def is_locked_out(self, ip: Optional[str], username: str) -> Tuple[bool, int]:
        """Kiem tra xem IP hoac tai khoan co dang bi khoa tam thoi khong."""
        if not settings.RATE_LIMIT_ENABLED:
            return False, 0

        now = time.time()
        with self._lock:
            self._cleanup_if_needed(now)
            keys = self._keys_for(ip, username)
            max_remaining = 0
            is_locked = False
            for k in keys:
                exp = self._lockouts.get(k)
                if exp and exp > now:
                    is_locked = True
                    rem = int(exp - now)
                    if rem > max_remaining:
                        max_remaining = rem

            return is_locked, max_remaining

    def record_failure(self, ip: Optional[str], username: str) -> Tuple[bool, int]:
        """Ghi nhan 1 lan dang nhap that bai. Tra ve (vua_bi_khoa, thoi_gian_con_lai)."""
        if not settings.RATE_LIMIT_ENABLED:
            return False, 0

        now = time.time()
        with self._lock:
            self._cleanup_if_needed(now)
            keys = self._keys_for(ip, username)
            just_locked = False
            max_remaining = 0

            for k in keys:
                # Bo qua neu da bi khoa truoc do
                if k in self._lockouts and self._lockouts[k] > now:
                    rem = int(self._lockouts[k] - now)
                    if rem > max_remaining:
                        max_remaining = rem
                    continue

                times = self._failures.get(k, [])
                # Giu lai cac lan fail trong cua so window
                times = [t for t in times if now - t <= self.failure_window]
                times.append(now)
                self._failures[k] = times

                if len(times) >= self.max_failures:
                    # Kich hoat khoa
                    exp = now + self.lockout_duration
                    self._lockouts[k] = exp
                    just_locked = True
                    rem = int(self.lockout_duration)
                    if rem > max_remaining:
                        max_remaining = rem

            return just_locked, max_remaining

    def record_success(self, ip: Optional[str], username: str) -> None:
        """Xoa bo dem that bai khi dang nhap thanh cong."""
        with self._lock:
            keys = self._keys_for(ip, username)
            for k in keys:
                self._failures.pop(k, None)
                self._lockouts.pop(k, None)

    def _cleanup_if_needed(self, now: float) -> None:
        # Don dep moi 10 phut
        if now - self._last_cleanup < 600:
            return
        self._last_cleanup = now
        expired_lockouts = [k for k, exp in self._lockouts.items() if exp <= now]
        for k in expired_lockouts:
            del self._lockouts[k]

        for k in list(self._failures.keys()):
            times = [t for t in self._failures[k] if now - t <= self.failure_window]
            if times:
                self._failures[k] = times
            else:
                del self._failures[k]


class SlidingWindowRateLimiter:
    """Gioi han tan suat goi API theo dia chi IP trong cua so truot (Sliding Window)."""

    def __init__(self, default_limit: int = 120, window_seconds: int = 60):
        self.default_limit = default_limit
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._requests: dict[str, list[float]] = {}
        self._last_cleanup = time.time()

    def check_request(
        self, ip: str, limit: Optional[int] = None
    ) -> Tuple[bool, int, int]:
        """
        Kiem tra request tu IP co duoc phep khong.
        Tra ve: (is_allowed, remaining_requests, retry_after)
        """
        if not settings.RATE_LIMIT_ENABLED or not ip:
            return True, 999, 0

        max_req = limit or self.default_limit
        now = time.time()

        with self._lock:
            self._cleanup_if_needed(now)
            times = self._requests.get(ip, [])
            times = [t for t in times if now - t < self.window_seconds]

            if len(times) >= max_req:
                oldest = times[0]
                retry_after = max(1, int(self.window_seconds - (now - oldest)))
                return False, 0, retry_after

            times.append(now)
            self._requests[ip] = times
            remaining = max(0, max_req - len(times))
            return True, remaining, 0

    def _cleanup_if_needed(self, now: float) -> None:
        if now - self._last_cleanup < 300:
            return
        self._last_cleanup = now
        for ip in list(self._requests.keys()):
            times = [t for t in self._requests[ip] if now - t < self.window_seconds]
            if times:
                self._requests[ip] = times
            else:
                del self._requests[ip]


# Singletons dung chung toan ung dung
login_protector = LoginBruteForceProtector(
    max_failures=settings.LOGIN_MAX_FAILURES,
    failure_window_seconds=300,
    lockout_duration_seconds=settings.LOGIN_LOCKOUT_SECONDS,
)

api_rate_limiter = SlidingWindowRateLimiter(
    default_limit=settings.API_RATE_LIMIT_PER_MINUTE,
    window_seconds=60,
)
