"""Protocol contracts — implement these to plug in your own backends."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class Principal:
    """Authenticated identity."""

    id: str
    roles: frozenset[str] = field(default_factory=frozenset)
    tenant_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class AuditEvent:
    """Append-only audit record."""

    actor: str
    action: str
    payload: dict[str, Any]
    resource_type: str | None = None
    resource_id: str | None = None
    tenant_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@runtime_checkable
class AuthBackend(Protocol):
    def authenticate(self, token: str) -> Principal | None:
        """Return a principal for a valid token, else None."""

    def authorize(
        self,
        principal: Principal,
        action: str,
        resource: str | None = None,
    ) -> bool:
        """Return True if principal may perform action on resource."""


@runtime_checkable
class AuditBackend(Protocol):
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
        """Persist an audit event; return the stored event."""

    def list(
        self,
        *,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Return recent events (newest first)."""


@runtime_checkable
class QueueBackend(Protocol):
    def enqueue(self, topic: str, message: dict[str, Any]) -> str:
        """Enqueue message; return message id."""

    def dequeue(self, topic: str, timeout_seconds: float = 0) -> dict[str, Any] | None:
        """Pop one message; None if empty / timeout."""

    def depth(self, topic: str) -> int:
        """Approximate queue depth."""
