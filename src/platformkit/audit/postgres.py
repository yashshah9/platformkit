"""Postgres audit log (optional extra)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from platformkit.protocols import AuditEvent

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS platformkit_audit_events (
    id BIGSERIAL PRIMARY KEY,
    actor TEXT NOT NULL,
    action TEXT NOT NULL,
    payload JSONB NOT NULL,
    resource_type TEXT,
    resource_id TEXT,
    tenant_id TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""

_CREATE_INDEX = """
CREATE INDEX IF NOT EXISTS platformkit_audit_tenant_created
    ON platformkit_audit_events (tenant_id, created_at DESC)
"""


class PostgresAudit:
    """Append-only audit table. Requires `platformkit[postgres]`."""

    def __init__(self, dsn: str, *, ensure_schema: bool = True) -> None:
        try:
            import psycopg
            from psycopg import errors as pg_errors
        except ImportError as exc:  # pragma: no cover
            raise ImportError(
                "PostgresAudit requires psycopg. Install platformkit[postgres]."
            ) from exc
        self._psycopg = psycopg
        self._pg_errors = pg_errors
        self._dsn = dsn
        if ensure_schema:
            self._ensure_schema()

    def _connect(self) -> Any:
        return self._psycopg.connect(self._dsn)

    def _ensure_schema(self) -> None:
        # Concurrent startups (API + worker) can race on CREATE; ignore duplicates.
        for stmt in (_CREATE_TABLE, _CREATE_INDEX):
            try:
                with self._connect() as conn:
                    conn.execute(stmt)
                    conn.commit()
            except self._pg_errors.DuplicateTable:
                pass
            except self._pg_errors.UniqueViolation:
                pass
            except self._pg_errors.DuplicateObject:
                pass

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
            payload=payload,
            resource_type=resource_type,
            resource_id=resource_id,
            tenant_id=tenant_id,
        )
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO platformkit_audit_events
                    (actor, action, payload, resource_type, resource_id, tenant_id, created_at)
                VALUES (%s, %s, %s::jsonb, %s, %s, %s, %s)
                """,
                (
                    event.actor,
                    event.action,
                    json.dumps(event.payload),
                    event.resource_type,
                    event.resource_id,
                    event.tenant_id,
                    event.created_at,
                ),
            )
            conn.commit()
        return event

    def list(
        self,
        *,
        tenant_id: str | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        limit = max(1, min(limit, 1000))
        with self._connect() as conn:
            if tenant_id is None:
                rows = conn.execute(
                    """
                    SELECT actor, action, payload, resource_type, resource_id, tenant_id, created_at
                    FROM platformkit_audit_events
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (limit,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT actor, action, payload, resource_type, resource_id, tenant_id, created_at
                    FROM platformkit_audit_events
                    WHERE tenant_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (tenant_id, limit),
                ).fetchall()
        out: list[AuditEvent] = []
        for row in rows:
            payload = row[2]
            if isinstance(payload, str):
                payload = json.loads(payload)
            created = row[6]
            if isinstance(created, datetime) and created.tzinfo is None:
                created = created.replace(tzinfo=UTC)
            out.append(
                AuditEvent(
                    actor=row[0],
                    action=row[1],
                    payload=dict(payload),
                    resource_type=row[3],
                    resource_id=row[4],
                    tenant_id=row[5],
                    created_at=created,
                )
            )
        return out
