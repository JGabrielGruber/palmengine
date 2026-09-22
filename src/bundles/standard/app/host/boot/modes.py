"""
Boot modes — presets over composition + deployment + schedule strictness (0.59.2+).

Modes are not a fourth composition root. They select axes and system-log defaults.
Dogfood entry:
- 0.59.6 — ``ApplicationHost.for_mode("safe"|"test")`` CI isolation green bar
- 0.59.7 — ``dev`` / ``prod`` + shape presets (cli/mcp/worker/server/all_in_one)

See docs/VISION-0.59.md §6.3 and ADR-028 D3.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal, Self

from bundles.standard.app.host.composition import CompositionProfile, composition_profile_from_name
from bundles.standard.app.host.roles import DeploymentProfile
from palm.system.log import (
    LEVEL_LIFECYCLE,
    LEVEL_OPERATE,
    LEVEL_SYSTEM,
    SystemLog,
    get_system_log,
)

BootModeName = Literal[
    "safe",
    "test",
    "dev",
    "prod",
    "cli",
    "mcp",
    "worker",
    "server",
    "all_in_one",
]


@dataclass(frozen=True)
class BootMode:
    """Named phenotype: membership axes + log defaults + start strictness."""

    name: str
    description: str
    composition: CompositionProfile
    deployment: DeploymentProfile
    system_log_level: int = LEVEL_LIFECYCLE
    #: None → leave SystemLog console policy to env/pytest defaults.
    system_log_console: bool | None = None
    recover_on_start: bool = True

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "system_log_level": self.system_log_level,
            "recover_on_start": self.recover_on_start,
            "composition_services": list(self.composition.services),
            "composition_surfaces": list(self.composition.surfaces),
            "composition_capabilities": sorted(self.composition.capabilities),
            "deployment_roles": sorted(self.deployment.roles),
            "deployment_server": self.deployment.server,
        }

    # ── Core modes ───────────────────────────────────────────────────────────

    @classmethod
    def safe(cls) -> Self:
        """Minimal truth; CI isolation; no surfaces; no background drain."""
        return cls(
            name="safe",
            description="Minimal truth; CI isolation; no surfaces; no background drain",
            composition=composition_profile_from_name("embedded"),
            deployment=DeploymentProfile.all_in_one(),
            system_log_level=LEVEL_LIFECYCLE,
            recover_on_start=False,
        )

    @classmethod
    def test(cls) -> Self:
        """Deterministic host; recover off by default; quiet-friendly log level."""
        return cls(
            name="test",
            description="Deterministic host; recover off by default",
            composition=composition_profile_from_name("embedded"),
            deployment=DeploymentProfile.all_in_one(),
            system_log_level=LEVEL_LIFECYCLE,
            system_log_console=False,
            recover_on_start=False,
        )

    @classmethod
    def dev(cls) -> Self:
        """Full local dogfood — richer system log."""
        return cls(
            name="dev",
            description="Full local dogfood",
            composition=composition_profile_from_name("all_in_one"),
            deployment=DeploymentProfile.all_in_one(),
            system_log_level=LEVEL_OPERATE,
            recover_on_start=True,
        )

    @classmethod
    def prod(cls) -> Self:
        """Strict operate; declared surfaces via deployment/server path."""
        return cls(
            name="prod",
            description="Strict operate; declared surfaces only",
            composition=composition_profile_from_name("server"),
            deployment=DeploymentProfile.server_only(),
            system_log_level=LEVEL_SYSTEM,
            recover_on_start=True,
        )

    # ── Shape presets (map existing composition / deployment) ────────────────

    @classmethod
    def cli(cls) -> Self:
        return cls(
            name="cli",
            description="CLI / REPL shape",
            composition=composition_profile_from_name("cli"),
            deployment=DeploymentProfile.all_in_one(),
            system_log_level=LEVEL_SYSTEM,
            recover_on_start=True,
        )

    @classmethod
    def mcp(cls) -> Self:
        return cls(
            name="mcp",
            description="MCP operator shape",
            composition=composition_profile_from_name("mcp"),
            deployment=DeploymentProfile.all_in_one(),
            system_log_level=LEVEL_SYSTEM,
            recover_on_start=True,
        )

    @classmethod
    def worker(cls) -> Self:
        return cls(
            name="worker",
            description="Headless worker shape",
            composition=composition_profile_from_name("worker"),
            deployment=DeploymentProfile.worker_only(),
            system_log_level=LEVEL_SYSTEM,
            recover_on_start=True,
        )

    @classmethod
    def server(cls) -> Self:
        return cls(
            name="server",
            description="HTTP server shape",
            composition=composition_profile_from_name("server"),
            deployment=DeploymentProfile.server_only(),
            system_log_level=LEVEL_SYSTEM,
            recover_on_start=True,
        )

    @classmethod
    def all_in_one(cls) -> Self:
        return cls(
            name="all_in_one",
            description="Collapsed full host (legacy default phenotype)",
            composition=composition_profile_from_name("all_in_one"),
            deployment=DeploymentProfile.all_in_one(),
            system_log_level=LEVEL_LIFECYCLE,
            recover_on_start=True,
        )


_REGISTRY: dict[str, BootMode] = {}


def _ensure_registry() -> dict[str, BootMode]:
    if not _REGISTRY:
        for factory in (
            BootMode.safe,
            BootMode.test,
            BootMode.dev,
            BootMode.prod,
            BootMode.cli,
            BootMode.mcp,
            BootMode.worker,
            BootMode.server,
            BootMode.all_in_one,
        ):
            mode = factory()
            _REGISTRY[mode.name] = mode
    return _REGISTRY


def list_boot_modes() -> tuple[str, ...]:
    return tuple(sorted(_ensure_registry()))


def get_boot_mode(name: str) -> BootMode:
    key = str(name).strip().lower()
    reg = _ensure_registry()
    if key not in reg:
        raise ValueError(f"Unknown boot mode {name!r}; expected one of {sorted(reg)}")
    return reg[key]


def resolve_boot_mode(mode: BootMode | str | None) -> BootMode | None:
    if mode is None:
        return None
    if isinstance(mode, BootMode):
        return mode
    return get_boot_mode(mode)


def apply_boot_mode_to_system_log(
    mode: BootMode | None,
    *,
    force: bool = False,
    log: SystemLog | None = None,
) -> SystemLog:
    """Configure process SystemLog from mode defaults.

    Explicit ``PALM_SYSTEM_LOG_LEVEL`` wins unless ``force=True`` — agents and
    operators keep an override lever. Console: mode may force off (test); env
    ``PALM_SYSTEM_LOG`` still forces on/off when set.
    """
    slog = log if log is not None else get_system_log()
    if mode is None:
        return slog

    env_level = (os.environ.get("PALM_SYSTEM_LOG_LEVEL") or "").strip()
    if force or not env_level:
        slog.configure(level=mode.system_log_level)

    env_console = (os.environ.get("PALM_SYSTEM_LOG") or "").strip()
    if mode.system_log_console is not None and not env_console:
        slog.configure(console=mode.system_log_console)
    return slog


__all__ = [
    "BootMode",
    "BootModeName",
    "apply_boot_mode_to_system_log",
    "get_boot_mode",
    "list_boot_modes",
    "resolve_boot_mode",
]
