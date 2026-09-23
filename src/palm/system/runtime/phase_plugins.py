"""
System start phase: install package names when the caller supplies an installer.

Subject: plugin registries. This phase does not choose packages and does not
import ``palm.common.plugins``.

No ``composition_packages`` mapping: the phase returns. A mapping calls the
``plugin_install`` callable from the same options. A mapping without that
callable fails closed.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.system.boot.context import BootContext
from palm.system.boot.definition import PhaseDefinition

_PACKAGE_KEYS = ("kits", "patterns", "providers", "runners", "storages", "transforms")


def run(_ctx: BootContext, options: Mapping[str, Any]) -> None:
    raw = options.get("composition_packages")
    if not isinstance(raw, Mapping):
        return
    installer = options.get("plugin_install")
    if not callable(installer):
        raise RuntimeError(
            "system.plugins.ensure: composition_packages is set and plugin_install is missing"
        )
    names = {key: tuple(raw[key]) for key in _PACKAGE_KEYS}
    installer(
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
