"""Runtime summary helpers for CLI status and doctor output."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from palm.app.host.application_host import ApplicationHost


def format_runtime_line(host: ApplicationHost) -> str:
    """Single-line runtime summary for panels."""
    if not host.is_started:
        return "[red]stopped[/]"
    names = host.running_runtimes()
    if not names:
        return "[red]no runtimes[/]"
    joined = ", ".join(names)
    return f"[green]{joined}[/] — started"