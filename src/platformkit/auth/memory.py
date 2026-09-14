"""In-memory auth for tests and local demos."""

from __future__ import annotations

from platformkit.protocols import Principal


class MemoryAuth:
    """Map token → Principal. Default authorize: admin role or explicit grants."""

    def __init__(
        self,
        principals: dict[str, Principal] | None = None,
        *,
        grants: dict[str, set[str]] | None = None,
    ) -> None:
        self._principals = dict(principals or {})
        # principal_id → set of "action" or "action:resource"
        self._grants = {k: set(v) for k, v in (grants or {}).items()}

    def register(self, token: str, principal: Principal) -> None:
        self._principals[token] = principal

    def authenticate(self, token: str) -> Principal | None:
        return self._principals.get(token)

    def authorize(
        self,
        principal: Principal,
        action: str,
        resource: str | None = None,
    ) -> bool:
        if "admin" in principal.roles:
            return True
        allowed = self._grants.get(principal.id, set())
        if action in allowed:
            return True
        if resource is not None and f"{action}:{resource}" in allowed:
            return True
        return False
