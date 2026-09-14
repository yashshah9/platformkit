"""Example: custom auth plugin injected without entry points."""

from platformkit import PlatformKit, Principal
from platformkit.audit.memory import MemoryAudit
from platformkit.queue.memory import MemoryQueue


class HeaderUserAuth:
    """Pretend corporate SSO: token format `user:<id>`."""

    def authenticate(self, token: str) -> Principal | None:
        if not token.startswith("user:"):
            return None
        user_id = token.removeprefix("user:")
        return Principal(id=user_id, roles=frozenset({"member"}), tenant_id="acme")

    def authorize(self, principal: Principal, action: str, resource: str | None = None) -> bool:
        del resource
        return action.startswith("runs:")


if __name__ == "__main__":
    kit = PlatformKit(auth=HeaderUserAuth(), audit=MemoryAudit(), queue=MemoryQueue())
    p = kit.auth.authenticate("user:ada")
    assert p is not None
    assert kit.auth.authorize(p, "runs:create")
    print("custom plugin ok", p)
