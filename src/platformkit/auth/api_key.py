"""Simple API-key auth driver."""

from __future__ import annotations

from platformkit.protocols import Principal


class ApiKeyAuth:
    """Authenticate via static API keys.

    Config example::

        {"driver": "api_key", "keys": {"sk_test": "tenant-a"}, "admin_keys": ["sk_admin"]}

    `keys` maps token → tenant_id (principal id defaults to tenant_id).
    `admin_keys` get role admin.
    """

    def __init__(
        self,
        keys: dict[str, str] | None = None,
        *,
        admin_keys: list[str] | None = None,
        default_role: str = "member",
    ) -> None:
        self._keys = dict(keys or {})
        self._admin = set(admin_keys or [])
        self._default_role = default_role

    def authenticate(self, token: str) -> Principal | None:
        if token in self._admin:
            tenant: str = self._keys.get(token) or "admin"
            return Principal(
                id=f"key:{token[:8]}",
                roles=frozenset({"admin", self._default_role}),
                tenant_id=tenant,
            )
        mapped = self._keys.get(token)
        if mapped is None:
            return None
        return Principal(
            id=f"key:{token[:8]}",
            roles=frozenset({self._default_role}),
            tenant_id=mapped,
        )

    def authorize(
        self,
        principal: Principal,
        action: str,
        resource: str | None = None,
    ) -> bool:
        del principal, action, resource
        # MVP: any authenticated principal is allowed; tighten per-app.
        return True
