"""
System start phase: optional runtime bind (system.bind).

Reads the ``runtime_binding`` registry on the system instance.
A missing registry skips the phase. There is no process-wide fallback.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.system.boot.context import BootContext
from palm.system.boot.definition import PhaseDefinition
from palm.system.boot.shell import resolve_shell
from palm.system.boot.skip import PhaseSkip


def run(ctx: BootContext, _options: Mapping[str, Any]) -> None:
    shell = resolve_shell(ctx)
    registries = getattr(shell, "registries", None)
    if registries is None or "runtime_binding" not in registries.names():
        raise PhaseSkip("no_runtime_binding")
    table = registries.require("runtime_binding")
    names = table.names()
    if not names:
        raise PhaseSkip("no_runtime_binding")
    for name in names:
        table.get(name)(shell)


DEFINITION = PhaseDefinition(
    id="system.bind",
    run=run,
    description="Optional palm provider bind",
)

__all__ = ["DEFINITION", "run"]
