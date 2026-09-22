"""
Host boot — modes + host schedule handlers (0.59.4).

System phase protocol + walker live in ``palm.system.boot``.
Host *start law* (handlers, modes) lives here. ApplicationHost is the shell.

**Ownership:** host schedule owns composition-root start order. Collaborators
(kernel, spawner, wire, recovery) are tools. Clean the host soup into seats;
do not grow private boot order on ApplicationHost.
"""

from __future__ import annotations

from bundles.standard.app.host.boot.host_schedule import build_host_handlers
from bundles.standard.app.host.boot.modes import (
    BootMode,
    BootModeName,
    apply_boot_mode_to_system_log,
    get_boot_mode,
    list_boot_modes,
    resolve_boot_mode,
)
from bundles.standard.app.host.boot.system_log_phase import make_host_system_log_handler

__all__ = [
    "BootMode",
    "BootModeName",
    "apply_boot_mode_to_system_log",
    "build_host_handlers",
    "get_boot_mode",
    "list_boot_modes",
    "make_host_system_log_handler",
    "resolve_boot_mode",
]
