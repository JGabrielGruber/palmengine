"""
Host early seat: SystemLog configure from boot mode (0.59.2).

Linux-inspired: early console before the rest of the host schedule.
System schedule seat lives in ``palm.system.log.phase_ready`` (subject-local).
"""

from __future__ import annotations

from collections.abc import Callable

from bundles.standard.app.host.boot.modes import BootMode, apply_boot_mode_to_system_log
from palm.system.boot.context import BootContext


def make_host_system_log_handler(
    mode: BootMode | None,
) -> Callable[[BootContext], None]:
    """Host schedule: ``host.system_log`` — configure log, record mode."""

    def _handler(ctx: BootContext) -> None:
        if mode is not None:
            ctx.mode = mode.name
        slog = apply_boot_mode_to_system_log(mode)
        # Lifecycle level so test/safe modes still see early console readiness.
        slog.info(
            "system_log.ready",
            "system log ready (host schedule)",
            schedule="host",
            mode=ctx.mode,
            log_level=slog.level,
        )

    return _handler


__all__ = [
    "make_host_system_log_handler",
]
