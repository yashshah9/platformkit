# platformkit

Pluggable **auth**, **audit**, and **queue** primitives. Apps depend on protocols; users pick a built-in driver or plug in their own.

## Why

Portfolio/production apps need the same boring infrastructure repeatedly. `platformkit` keeps that shared without forcing a monolith:

- Use our drivers (`api_key`, `memory`, `postgres`, `redis`)
- Or register your own via Python entry points / direct injection
- Swap backends with config — no app rewrite

## 60-second try

```bash
pip install -e ".[dev]"
python -c "
from platformkit import PlatformKit
kit = PlatformKit.from_config({
    'auth': {'driver': 'api_key', 'keys': {'dev': 'admin'}},
    'audit': {'driver': 'memory'},
    'queue': {'driver': 'memory'},
})
principal = kit.auth.authenticate('dev')
kit.audit.emit(actor=principal.id, action='demo.ping', payload={'ok': True})
kit.queue.enqueue('jobs', {'type': 'ping'})
print(kit.queue.dequeue('jobs'))
"
```

## Plugin model

| Concern | Protocol | Built-ins |
|---------|----------|-----------|
| Auth | `AuthBackend` | `memory`, `api_key` |
| Audit | `AuditBackend` | `memory`, `postgres` |
| Queue | `QueueBackend` | `memory`, `redis` |

### Config

```python
PlatformKit.from_config({
    "auth": {"driver": "api_key", "keys": {"sk_live_…": "tenant-1"}},
    "audit": {"driver": "postgres", "dsn": "postgresql://…"},
    "queue": {"driver": "redis", "url": "redis://localhost:6379/0"},
})
```

### Inject your own

```python
from platformkit import PlatformKit
from platformkit.protocols import AuthBackend, Principal

class CorporateSSO:
    def authenticate(self, token: str) -> Principal | None: ...
    def authorize(self, principal: Principal, action: str, resource: str | None = None) -> bool: ...

kit = PlatformKit(auth=CorporateSSO(), audit=..., queue=...)
```

### Entry-point plugins

Third-party packages can expose:

```toml
[project.entry-points."platformkit.auth"]
acme_sso = "acme_platform.sso:AcmeAuth"
```

Then `"driver": "acme_sso"` resolves automatically.

## Design rules

- Dumb and small — no framework magic, no shared product DB schema beyond audit rows
- Protocols are the contract; drivers are swappable
- In-memory drivers for tests; Redis/Postgres only when extras installed

## Docker driver tests

```bash
docker compose up --build --abort-on-container-exit integration
```

Runs Redis + Postgres round-trips for queue/audit drivers.
