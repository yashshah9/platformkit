"""Entry-point + dict config loading for pluggable backends."""

from __future__ import annotations

from importlib.metadata import entry_points
from typing import Any, TypeVar

T = TypeVar("T")

GROUP = {
    "auth": "platformkit.auth",
    "audit": "platformkit.audit",
    "queue": "platformkit.queue",
}


def load_driver(kind: str, driver: str, options: dict[str, Any] | None = None) -> Any:
    """Instantiate a driver by entry-point name.

    Built-ins ship in this package. Third parties register the same groups.
    """
    if kind not in GROUP:
        raise ValueError(f"Unknown plugin kind: {kind}")
    eps = entry_points(group=GROUP[kind])
    match = next((ep for ep in eps if ep.name == driver), None)
    if match is None:
        known = sorted(ep.name for ep in eps)
        raise ValueError(f"Unknown {kind} driver {driver!r}. Known: {known}")
    cls = match.load()
    opts = options or {}
    return cls(**opts)


def split_config(raw: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Pull `driver` out; remaining keys are constructor kwargs."""
    if "driver" not in raw:
        raise ValueError("Config block requires 'driver'")
    options = {k: v for k, v in raw.items() if k != "driver"}
    return str(raw["driver"]), options
