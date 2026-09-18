"""In-memory audit log."""

from __future__ import annotations

from typing import Any

from platformkit.protocols import AuditEvent


class MemoryAudit:
    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def emit(
        self,
        *,
        actor: str,
        action: str,
        payload: dict[str, Any],
        resource_type: str | None = None,
        resource_id: str | None = None,
        tenant_id: str | None = None,
    ) -> AuditEvent:
        event = AuditEvent(
            actor=actor,
            action=action,
            payload=dict(payload),
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
        )
        self._events.append(event)
        return event

    def list(
        self,
        *,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        items = self._events
        if tenant_id is not None:
            items = [e for e in items if e.tenant_id == tenant_id]
        newest_first = list(reversed(items))
        return newest_first[: max(1, limit)]
