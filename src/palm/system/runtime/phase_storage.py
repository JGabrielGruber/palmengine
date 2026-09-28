"""
System start phase: storage select (system.storage.select).

Subject: attach the storage backend the bundle already opened.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.system.boot.context import BootContext
from palm.system.boot.definition import PhaseDefinition
from palm.system.boot.shell import resolve_shell
from palm.system.bound import BoundDrivers


def select_system_storage(
    shell: Any,
    options: Mapping[str, Any] | None = None,
) -> Any:
    """Attach the bound storage backend. Does not load or default one."""
    opts = dict(options or {})
    drivers = opts.get("drivers")
    if not isinstance(drivers, BoundDrivers):
        raise RuntimeError("system storage select requires bound drivers")
    shell.storage.attach(drivers.storage)
    return shell.storage


def run(ctx: BootContext, options: Mapping[str, Any]) -> None:
    storage = select_system_storage(resolve_shell(ctx), options)
    ctx.publish(storage=storage)


DEFINITION = PhaseDefinition(
    id="system.storage.select",
    run=run,
    description="attach the bound storage backend",
)

__all__ = ["DEFINITION", "run", "select_system_storage"]
