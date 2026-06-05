"""
Engine diagnostics — health, registries, storage, definitions, and instances.
"""

from __future__ import annotations

from palm import __version__
from palm.core.registry import pattern_registry, provider_registry, storage_registry
from palm.runtimes.cli_pkg.context import CliContext
from palm.runtimes.cli_pkg.display import render_definition_catalog, render_instance_table


def run_doctor(ctx: CliContext) -> int:
    """Print a full diagnostic report; return 0 when the runtime is healthy."""
    from rich.panel import Panel
    from rich.table import Table

    console = ctx.console
    runtime = ctx.runtime
    issues: list[str] = []

    if not runtime.is_started:
        issues.append("EmbeddedRuntime is not started")

    storage = runtime.storage
    backend_name = storage.backend_name or "(none)"
    backend_open = (
        storage.backend is not None and storage.backend.is_open
        if storage.backend is not None
        else False
    )
    if not backend_open:
        issues.append(f"Storage backend {backend_name!r} is not open")

    console.print(
        Panel(
            f"[bold]Palm Engine v{__version__}[/]\n"
            f"Runtime: embedded — {'[green]started[/]' if runtime.is_started else '[red]stopped[/]'}\n"
            f"Storage: {backend_name} — "
            f"{'[green]ready[/]' if backend_open else '[red]unavailable[/]'}",
            title="Engine Health",
            border_style="green" if not issues else "yellow",
        )
    )

    reg_table = Table(title="Registered Plugins", show_lines=True)
    reg_table.add_column("Registry", style="cyan")
    reg_table.add_column("Names")
    reg_table.add_row("patterns", ", ".join(sorted(pattern_registry.names())) or "—")
    reg_table.add_row("providers", ", ".join(sorted(provider_registry.names())) or "—")
    reg_table.add_row("storages", ", ".join(sorted(storage_registry.names())) or "—")
    console.print(reg_table)

    flows = runtime.repository.list_flows()
    processes = runtime.repository.list_processes()
    inst_table = Table(title="Catalog & Persistence", show_lines=True)
    inst_table.add_column("Resource", style="cyan")
    inst_table.add_column("Count", justify="right")
    inst_table.add_column("Notes")
    inst_table.add_row("flow definitions", str(len(flows)), "in-memory + storage index")
    inst_table.add_row("process definitions", str(len(processes)), "")
    instances = runtime.instances.list_instances()
    inst_table.add_row("process instances", str(len(instances)), "durable snapshots")
    console.print(inst_table)

    render_definition_catalog(ctx)

    recent = sorted(instances, key=lambda i: i.updated_at, reverse=True)[:10]
    if recent:
        console.print("[bold]Recent instances[/] [dim](newest first, up to 10)[/]")
        render_instance_table(console, recent)
    else:
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
