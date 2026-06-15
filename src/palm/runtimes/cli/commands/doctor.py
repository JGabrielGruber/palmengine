"""
Engine diagnostics — health, registries, storage, definitions, and instances.
"""

from __future__ import annotations

from typing import Any

from palm import __version__
from palm.core.registry import pattern_registry, provider_registry, storage_registry
from palm.core.transform.registry import transform_registry
from palm.runtimes.cli.commands.views import render_definition_catalog, render_instance_table
from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.shared.instance_ops import is_terminal_status
from palm.runtimes.cli.shared.job_inspect import inspect_job
from palm.runtimes.cli.shared.settings import is_durable_storage
from palm.runtimes.cli.shared.startup import format_persistence_notice
from palm.runtimes.cli.tui.context import context_lines


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

    from palm.common.transforms import autoload as autoload_transforms

    autoload_transforms()

    reg_table = Table(title="Registered Plugins", show_lines=True)
    reg_table.add_column("Registry", style="cyan")
    reg_table.add_column("Names")
    reg_table.add_row("patterns", ", ".join(sorted(pattern_registry.names())) or "—")
    reg_table.add_row("providers", ", ".join(sorted(provider_registry.names())) or "—")
    reg_table.add_row("storages", ", ".join(sorted(storage_registry.names())) or "—")
    reg_table.add_row("transforms", ", ".join(sorted(transform_registry.names())) or "—")
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
        console.print(f"[bold]Active instances[/] [dim]({len(active)} non-terminal)[/]")
        render_instance_table(console, active[:10])
        _render_active_job_context(ctx, active[:5])
    elif summaries:
        console.print("[dim]No active instances — all persisted runs are terminal.[/]")

    render_definition_catalog(ctx)

    recent = summaries[:10]
    if recent and not active:
        console.print("[bold]Recent instances[/] [dim](newest first, up to 10)[/]")
        render_instance_table(console, recent)
    elif not summaries:
        console.print("[dim]No process instances yet — try[/] [cyan]flow start onboard[/]")

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


def _render_active_job_context(ctx: CliContext, active: list[Any]) -> None:
    """Show scope, branch, and schema detail for active instances."""
    from rich.panel import Panel

    console = ctx.console
    shown = 0
    for summary in active:
        try:
            job = ctx.job_for_instance(summary.instance_id)
        except Exception:
            continue
        ctx_lines = context_lines(job)
        job_ctx = inspect_job(job)
        if not ctx_lines and job_ctx.pattern == "unknown":
            continue
        title = summary.flow_name or summary.process_name or summary.instance_id[:12]
        body = "\n".join(ctx_lines) if ctx_lines else f"[dim]pattern[/] {job_ctx.pattern}"
        if job_ctx.prompt:
            body = f"[bold]{job_ctx.prompt}[/]\n\n{body}"
        console.print(
            Panel(
                body.strip(),
                title=f"[cyan]{title}[/] — {summary.status}",
                subtitle=summary.instance_id[:20],
                border_style="magenta" if job_ctx.pattern == "parallel" else "blue",
            )
        )
        shown += 1
    if shown:
        console.print(
            "[dim]Tip:[/] [cyan]status <id>[/] for full detail, "
            "[cyan]flow start parallel-demo[/] to try parallel branches"
        )
