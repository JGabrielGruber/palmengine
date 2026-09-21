"""
System start phase: install composition package names (system.plugins.ensure).

Subject: plugin registry (common); phase seat on system start.

The host passes ``composition_packages`` on start options. This phase calls
the install stroke with those names. A start with no package set installs
nothing — the system schedule does not choose a package set.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.common.plugins import ensure_core_plugins
from palm.system.boot.context import BootContext
from palm.system.boot.definition import PhaseDefinition

_PACKAGE_KEYS = ("kits", "patterns", "providers", "runners", "storages", "transforms")


def run(_ctx: BootContext, options: Mapping[str, Any]) -> None:
    raw = options.get("composition_packages")
    if not isinstance(raw, Mapping):
        return
    names = {key: tuple(raw[key]) for key in _PACKAGE_KEYS}
    ensure_core_plugins(
        kits=names["kits"],
        patterns=names["patterns"],
        providers=names["providers"],
        runners=names["runners"],
        storages=names["storages"],
        transforms=names["transforms"],
    )


DEFINITION = PhaseDefinition(
    id="system.plugins.ensure",
    run=run,
    description="install composition package names",
)

__all__ = ["DEFINITION", "run"]
