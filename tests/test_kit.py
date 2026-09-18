"""platformkit tests."""

from __future__ import annotations

import pytest

from platformkit import PlatformKit, Principal
from platformkit.auth.memory import MemoryAuth
from platformkit.plugins import load_driver


def test_from_config_memory_roundtrip() -> None:
    kit = PlatformKit.from_config(
        {
            "auth": {"driver": "api_key", "keys": {"dev-key": "tenant-1"}, "admin_keys": ["admin"]},
            "audit": {"driver": "memory"},
            "queue": {"driver": "memory"},
        }
    )
    principal = kit.auth.authenticate("dev-key")
    assert principal is not None
    assert principal.tenant_id == "tenant-1"
    assert kit.auth.authenticate("nope") is None

    admin = kit.auth.authenticate("admin")
    assert admin is not None
    assert "admin" in admin.roles

    kit.audit.emit(
        actor=principal.id,
        action="run.create",
        payload={"ok": True},
        tenant_id="tenant-1",
    )
    events = kit.audit.list(tenant_id="tenant-1")
    assert len(events) == 1
    assert events[0].action == "run.create"

    msg_id = kit.queue.enqueue("runs", {"run_id": "r1"})
    assert msg_id
    assert kit.queue.depth("runs") == 1
    msg = kit.queue.dequeue("runs")
    assert msg is not None
    assert msg["run_id"] == "r1"
    assert kit.queue.dequeue("runs") is None

    kit.queue.enqueue("runs", {"run_id": "r2"})
    kit.queue.enqueue("other", {"x": 1})
    assert hasattr(kit.queue, "clear")
    kit.queue.clear("runs")  # type: ignore[attr-defined]
    assert kit.queue.depth("runs") == 0
    assert kit.queue.depth("other") == 1
    kit.queue.clear()  # type: ignore[attr-defined]
    assert kit.queue.depth("other") == 0


def test_inject_custom_auth() -> None:
    auth = MemoryAuth(
        principals={"tok": Principal(id="u1", roles=frozenset({"member"}), tenant_id="t1")},
        grants={"u1": {"runs:read"}},
    )
    kit = PlatformKit.from_config(
        {
            "auth": {"driver": "memory"},
            "audit": {"driver": "memory"},
            "queue": {"driver": "memory"},
        }
    )
    # replace auth with custom instance (plugin injection pattern)
    kit = PlatformKit(auth=auth, audit=kit.audit, queue=kit.queue)
    p = kit.auth.authenticate("tok")
    assert p is not None
    assert kit.auth.authorize(p, "runs:read") is True
    assert kit.auth.authorize(p, "runs:write") is False


def test_unknown_driver() -> None:
    with pytest.raises(ValueError, match="Unknown auth driver"):
        load_driver("auth", "does-not-exist")


def test_missing_config_section() -> None:
    with pytest.raises(ValueError, match="Missing config"):
        PlatformKit.from_config({"auth": {"driver": "memory"}})
