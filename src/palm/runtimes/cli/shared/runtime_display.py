"""Runtime summary helpers for CLI status and doctor output."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from palm.app.host.application_host import ApplicationHost


def format_runtime_line(host: ApplicationHost) -> str:
    """Single-line runtime summary for panels."""
    plain = runtime_names_plain(host)
    if plain == "stopped":
        return "[red]stopped[/]"
    if plain == "no runtimes":
        return "[red]no runtimes[/]"
    return f"[green]{plain}[/] — started"


def runtime_names_plain(host: ApplicationHost) -> str:
    """Plain runtime names for tables (no Rich markup)."""
    if not host.is_started:
        return "stopped"
    names = host.running_runtimes()
    if not names:
        return "no runtimes"
    return ", ".join(names)