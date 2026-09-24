"""
System start phase: call the install callable the bundle passed.

This phase does not name plugin packages, bundles, or family tuples.
No ``plugin_install``: the phase returns. A non-callable value fails closed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.system.boot.context import BootContext
from palm.system.boot.definition import PhaseDefinition


def run(_ctx: BootContext, options: Mapping[str, Any]) -> None:
    installer = options.get("plugin_install")
    if installer is None:
        return
    if not callable(installer):
        raise RuntimeError("system.plugins.ensure: plugin_install is not callable")
    installer()


DEFINITION = PhaseDefinition(
    id="system.plugins.ensure",
    run=run,
    description="call plugin_install when the caller set it",
)

__all__ = ["DEFINITION", "run"]
