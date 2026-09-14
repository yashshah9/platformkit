"""Redis list queue (optional extra)."""

from __future__ import annotations

import json
import uuid
from typing import Any


class RedisQueue:
    """Simple LPUSH/BRPOP queue. Requires `platformkit[redis]`."""

    def __init__(self, url: str = "redis://localhost:6379/0", *, key_prefix: str = "pk") -> None:
        try:
            import redis
        except ImportError as exc:  # pragma: no cover
            raise ImportError("RedisQueue requires redis. Install platformkit[redis].") from exc
        self._redis = redis.Redis.from_url(url, decode_responses=True)
        self._prefix = key_prefix

    def _key(self, topic: str) -> str:
        return f"{self._prefix}:q:{topic}"

    def enqueue(self, topic: str, message: dict[str, Any]) -> str:
        msg_id = str(uuid.uuid4())
        envelope = json.dumps({"id": msg_id, "body": message})
        self._redis.lpush(self._key(topic), envelope)
        return msg_id

    def dequeue(self, topic: str, timeout_seconds: float = 0) -> dict[str, Any] | None:
        key = self._key(topic)
        raw: str | None
        if timeout_seconds and timeout_seconds > 0:
            item = self._redis.brpop(key, timeout=max(1, int(timeout_seconds)))
            if item is None:
                return None
            raw = str(item[1])
        else:
            popped = self._redis.rpop(key)
            if popped is None:
                return None
            raw = str(popped)
        envelope = json.loads(raw)
        body = envelope["body"]
        if not isinstance(body, dict):
            raise TypeError("queue message body must be a dict")
        return {"id": envelope["id"], **body}

    def depth(self, topic: str) -> int:
        return int(self._redis.llen(self._key(topic)))
