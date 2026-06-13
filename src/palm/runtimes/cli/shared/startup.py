"""
CLI startup messaging — persistence mode and configuration summary.
"""

from __future__ import annotations

from typing import Any

from palm.app.app import PalmApp
from palm.runtimes.cli.shared.settings import is_durable_storage


def format_persistence_notice(app: PalmApp) -> str:
    """Human-readable persistence summary for doctor and REPL startup."""
    backend = app.settings.storage_backend
    durable = is_durable_storage(backend)
    lines: list[str] = []

    if durable:
        data_dir = app.settings.data_dir
        lines.append(
            f"[green]Durable storage[/] — backend [cyan]{backend}[/]"
            + (f", data dir [cyan]{data_dir}[/]" if data_dir else "")
        )
        if app.settings.enable_state_snapshot:
            lines.append(
                "[green]State snapshots enabled[/] "
                f"(max {app.settings.max_snapshots_per_instance} per instance)"
            )
        else:
            lines.append(
                "[dim]State snapshots off[/] — set "
                "[cyan]PALM_ENABLE_STATE_SNAPSHOT=true[/] for history"
            )
    else:
        lines.append(
            "[yellow]In-memory storage[/] — " "[bold]state will NOT persist across restarts[/]"
        )
        lines.append(
            "[dim]Use[/] [cyan]--storage-backend filesystem[/] "
            "[dim]or[/] [cyan]PALM_STORAGE_BACKEND=filesystem[/] "
            "[dim]for durable instances[/]"
        )

    manager = app.instance_manager
    if manager.is_initialized:
        active = len(manager.active_instance_ids)
        lines.append(
            f"[dim]InstanceManager[/] — "
            f"{len(app.list_instance_summaries())} known, {active} active"
        )

    return "\n".join(lines)


def print_startup_banner(console: Any, app: PalmApp) -> None:
    """Print persistence notice when the CLI session starts."""
    from rich.panel import Panel

    console.print(
        Panel(
            format_persistence_notice(app),
            title="Persistence",
            border_style="green" if is_durable_storage(app.settings.storage_backend) else "yellow",
        )
    )
