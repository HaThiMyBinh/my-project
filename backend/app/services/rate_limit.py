# -*- coding: utf-8 -*-
"""Bộ giới hạn tần suất (sliding window) lưu trong bộ nhớ.

Dùng cho: chống dò mật khẩu ở đăng nhập, chống lạm dụng/tốn quota khi gọi AI.
Lưu ý: trạng thái nằm trong tiến trình; nếu chạy nhiều worker cần chuyển sang Redis.
"""
import threading
import time
from collections import defaultdict, deque
from typing import Callable, Deque, Dict, Optional, Tuple


class SlidingWindowLimiter:
    def __init__(self, max_events: int, window_seconds: float, clock: Callable[[], float] = time.monotonic):
        self.max_events = max_events
        self.window = window_seconds
        self._clock = clock
        self._events: Dict[str, Deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> Deque[float]:
        q = self._events[key]
        while q and now - q[0] >= self.window:
            q.popleft()
        return q

    def retry_after(self, key: str) -> int:
        """Số giây phải chờ nếu đang bị chặn, 0 nếu được phép."""
        with self._lock:
            now = self._clock()
            q = self._prune(key, now)
            if len(q) < self.max_events:
                return 0
            return max(1, int(self.window - (now - q[0])) + 1)

    def hit(self, key: str) -> None:
        with self._lock:
            now = self._clock()
            self._prune(key, now).append(now)

    def check_and_hit(self, key: str) -> Tuple[bool, int]:
        """Ghi nhận 1 lượt nếu còn hạn mức. Trả về (được_phép, số_giây_chờ)."""
        with self._lock:
            now = self._clock()
            q = self._prune(key, now)
            if len(q) >= self.max_events:
                return False, max(1, int(self.window - (now - q[0])) + 1)
            q.append(now)
            return True, 0

    def reset(self, key: Optional[str] = None) -> None:
        with self._lock:
            if key is None:
                self._events.clear()
            else:
                self._events.pop(key, None)
