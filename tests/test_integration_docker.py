"""Integration tests for redis/postgres drivers."""

from __future__ import annotations

import os

import pytest

from platformkit import PlatformKit

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_DOCKER_INTEGRATION") != "1",
    reason="Set RUN_DOCKER_INTEGRATION=1 with redis/postgres available",
)


def test_redis_queue_roundtrip() -> None:
    url = os.environ["PLATFORMKIT_REDIS_URL"]
    kit = PlatformKit.from_config(
        {
            "auth": {"driver": "api_key", "keys": {"k": "t"}},
            "audit": {"driver": "memory"},
            "queue": {"driver": "redis", "url": url, "key_prefix": "pktest"},
        }
    )
    topic = "integration"
    # drain
    while kit.queue.dequeue(topic) is not None:
        pass
    mid = kit.queue.enqueue(topic, {"hello": "world"})
    assert mid
    assert kit.queue.depth(topic) == 1
    msg = kit.queue.dequeue(topic)
    assert msg is not None
    assert msg["hello"] == "world"
    assert kit.queue.depth(topic) == 0


def test_postgres_audit_roundtrip() -> None:
    dsn = os.environ["PLATFORMKIT_POSTGRES_DSN"]
    kit = PlatformKit.from_config(
        {
            "auth": {"driver": "memory"},
            "audit": {"driver": "postgres", "dsn": dsn},
            "queue": {"driver": "memory"},
        }
    )
    kit.audit.emit(
        actor="tester",
        action="integration.ping",
        payload={"ok": True},
        tenant_id="tenant-x",
    )
    events = kit.audit.list(tenant_id="tenant-x", limit=5)
    assert events
    assert events[0].action == "integration.ping"
    assert events[0].payload["ok"] is True
