"""
Engine diagnostics — health, registries, storage, definitions, and instances.
"""

from __future__ import annotations

from palm import __version__
from palm.core.registry import pattern_registry, provider_registry, storage_registry
from palm.runtimes.cli_pkg.context import CliContext
from palm.runtimes.cli_pkg.display import render_definition_catalog, render_instance_table
from palm.runtimes.cli_pkg.instance_ops import is_terminal_status
from palm.runtimes.cli_pkg.settings import is_durable_storage
from palm.runtimes.cli_pkg.startup import format_persistence_notice


def run_doctor(ctx: CliContext) -> int:
    """Print a full diagnostic report; return 0 when the runtime is healthy."""
    from rich.panel import Panel
    from rich.table import Table

    console = ctx.console
    app = ctx.app
    issues: list[str] = []

    if not app.is_runtime_started():
        issues.append("CLI runtime is not started")

    storage = app.storage
    backend_name = storage.backend_name or "(none)"
    backend_open = (
        storage.backend is not None and storage.backend.is_open
        if storage.backend is not None
        else False
    )
    if not backend_open:
        issues.append(f"Storage backend {backend_name!r} is not open")

    persistence_style = "green" if is_durable_storage(backend_name) else "yellow"
    console.print(
        Panel(
            f"[bold]Palm Engine v{__version__}[/]\n"
            f"Runtime: embedded — "
            f"{'[green]started[/]' if app.is_runtime_started() else '[red]stopped[/]'}\n"
            f"Storage: {backend_name} — "
            f"{'[green]ready[/]' if backend_open else '[red]unavailable[/]'}",
            title="Engine Health",
            border_style="green" if not issues else "yellow",
        )
    )
    console.print(
        Panel(
            format_persistence_notice(app),
            title="Persistence",
            border_style=persistence_style,
        )
    )

    reg_table = Table(title="Registered Plugins", show_lines=True)
    reg_table.add_column("Registry", style="cyan")
    reg_table.add_column("Names")
    reg_table.add_row("patterns", ", ".join(sorted(pattern_registry.names())) or "—")
    reg_table.add_row("providers", ", ".join(sorted(provider_registry.names())) or "—")
    reg_table.add_row("storages", ", ".join(sorted(storage_registry.names())) or "—")
    console.print(reg_table)

    flows = app.list_flows()
    processes = app.list_processes()
    schema_flows = sum(1 for flow in flows if flow.has_state_schema)
    inst_table = Table(title="Catalog & Persistence", show_lines=True)
    inst_table.add_column("Resource", style="cyan")
    inst_table.add_column("Count", justify="right")
    inst_table.add_column("Notes")
    schema_note = f"{schema_flows} with state_schema" if schema_flows else "none with state_schema"
    inst_table.add_row("flow definitions", str(len(flows)), f"in-memory + storage ({schema_note})")
    inst_table.add_row("process definitions", str(len(processes)), "")
    summaries = app.list_instance_summaries()
    active = [item for item in summaries if not is_terminal_status(item.status)]
    inst_table.add_row("process instances", str(len(summaries)), "durable snapshots")
    inst_table.add_row(
        "active instances",
        str(len(active)),
        "non-terminal (running, waiting, pending)",
    )
    console.print(inst_table)

    if active:
        console.print(
            f"[bold]Active instances[/] [dim]({len(active)} non-terminal)[/]"
        )
        render_instance_table(console, active[:10])
    elif summaries:
        console.print("[dim]No active instances — all persisted runs are terminal.[/]")

    render_definition_catalog(ctx)

    recent = summaries[:10]
    if recent and not active:
        console.print("[bold]Recent instances[/] [dim](newest first, up to 10)[/]")
        render_instance_table(console, recent)
    elif not summaries:
        console.print("[dim]No process instances yet — try[/] [cyan]wizard start onboard[/]")

    if issues:
        console.print(
            Panel(
                "\n".join(f"• {item}" for item in issues),
                title="Issues",
                border_style="red",
            )
        )
        return 1

    console.print("[green]All checks passed.[/]")
    return 0