"""In-memory FIFO queue for tests."""

from __future__ import annotations

import time
import uuid
from collections import defaultdict, deque
from typing import Any


class MemoryQueue:
    def __init__(self) -> None:
        self._topics: dict[str, deque[dict[str, Any]]] = defaultdict(deque)

    def enqueue(self, topic: str, message: dict[str, Any]) -> str:
        msg_id = str(uuid.uuid4())
        envelope = {"id": msg_id, "body": message}
        self._topics[topic].append(envelope)
        return msg_id

    def dequeue(self, topic: str, timeout_seconds: float = 0) -> dict[str, Any] | None:
        deadline = time.monotonic() + max(timeout_seconds, 0)
        while True:
            bucket = self._topics.get(topic)
            if bucket:
                envelope = bucket.popleft()
                return {"id": envelope["id"], **envelope["body"]}
            if time.monotonic() >= deadline:
                return None
            time.sleep(0.01)

    def depth(self, topic: str) -> int:
        return len(self._topics.get(topic, ()))

    def clear(self, topic: str | None = None) -> None:
        """Drop queued messages (tests / admin reset)."""
        if topic is None:
            self._topics.clear()
        else:
            self._topics.pop(topic, None)
