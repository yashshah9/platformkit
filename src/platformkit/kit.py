"""Facade that holds auth + audit + queue backends."""

from __future__ import annotations

from typing import Any

from platformkit.plugins import load_driver, split_config
from platformkit.protocols import AuditBackend, AuthBackend, QueueBackend


class PlatformKit:
    """Bundle of swappable infrastructure backends."""

    def __init__(
        self,
        *,
        auth: AuthBackend,
        audit: AuditBackend,
        queue: QueueBackend,
    ) -> None:
        self.auth = auth
        self.audit = audit
        self.queue = queue

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> PlatformKit:
        """Build from a dict of `{auth|audit|queue: {driver, ...}}`."""
        missing = [k for k in ("auth", "audit", "queue") if k not in config]
        if missing:
            raise ValueError(f"Missing config sections: {missing}")

        auth_driver, auth_opts = split_config(config["auth"])
        audit_driver, audit_opts = split_config(config["audit"])
        queue_driver, queue_opts = split_config(config["queue"])

        return cls(
            auth=load_driver("auth", auth_driver, auth_opts),
            audit=load_driver("audit", audit_driver, audit_opts),
            queue=load_driver("queue", queue_driver, queue_opts),
        )
