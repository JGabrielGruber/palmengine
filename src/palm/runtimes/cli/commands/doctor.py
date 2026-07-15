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
from palm.runtimes.cli.shared.runtime_display import format_runtime_line
from palm.runtimes.cli.shared.settings import is_durable_storage
from palm.runtimes.cli.shared.startup import format_persistence_notice
from palm.runtimes.cli.tui.context import context_lines


def run_doctor(ctx: CliContext) -> int:
    """Print a full diagnostic report; return 0 when the runtime is healthy."""
    from rich.panel import Panel
    from rich.table import Table

    console = ctx.console
    app = ctx.app
    host = ctx.host
    issues: list[str] = []

    if not ctx.is_runtime_started():
        issues.append("ApplicationHost runtimes are not started")

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
            f"Runtime: {format_runtime_line(host)}\n"
            f"Host roles: {', '.join(sorted(host.profile.roles))}\n"
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

    from palm.common.resource.catalog import ResourceCatalog

    resource_catalog = ResourceCatalog(app.repository())
    catalog_entries = resource_catalog.entries()
    if catalog_entries:
        resource_table = Table(title="Resource Providers & Actions", show_lines=True)
        resource_table.add_column("Resource", style="green")
        resource_table.add_column("Provider", style="cyan")
        resource_table.add_column("Action")
        resource_table.add_column("Provider Actions", style="dim")
        for entry in catalog_entries[:20]:
            resource_table.add_row(
                entry.name,
                entry.provider,
                entry.action,
                ", ".join(entry.provider_actions) or "—",
            )
        console.print(resource_table)

    from palm.common.transforms.catalog import TRANSFORM_CATALOG

    transform_names = sorted(transform_registry.names())
    if transform_names:
        tx_table = Table(title="Transform Rules", show_lines=True)
        tx_table.add_column("Rule", style="cyan", no_wrap=True)
        tx_table.add_column("Description")
        for name in transform_names:
            tx_table.add_row(name, TRANSFORM_CATALOG.get(name, "Registered transform rule"))
        console.print(tx_table)

    flows = app.list_flows()
    processes = app.list_processes()
    resources = app.list_resources()
    schema_flows = sum(1 for flow in flows if flow.has_state_schema)
    schema_resources = sum(1 for item in resources if item.has_schemas)
    inst_table = Table(title="Catalog & Persistence", show_lines=True)
    inst_table.add_column("Resource", style="cyan")
    inst_table.add_column("Count", justify="right")
    inst_table.add_column("Notes")
    schema_note = f"{schema_flows} with state_schema" if schema_flows else "none with state_schema"
    inst_table.add_row("flow definitions", str(len(flows)), f"in-memory + storage ({schema_note})")
    inst_table.add_row("process definitions", str(len(processes)), "")
    resource_note = (
        f"{schema_resources} with input/output schema"
        if schema_resources
        else "declarative contracts (invoke in 0.12 Phase 2+)"
    )
    inst_table.add_row("resource definitions", str(len(resources)), resource_note)
    summaries = ctx.list_instance_summaries()
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

    if hasattr(host, "ops_status"):
        try:
            ops = host.ops_status()
        except Exception:
            ops = {}
        if ops:
            ops_table = Table(title="Ops", show_lines=True)
            ops_table.add_column("Item", style="cyan")
            ops_table.add_column("Value", style="green")
            ops_table.add_row("invoke (short)", str(ops.get("invoke_route_short", "—")))
            ops_table.add_row("storage", str(ops.get("storage_backend", "—")))
            ops_table.add_row(
                "durable storage",
                "yes" if ops.get("storage_durable") else "no",
            )
            if ops.get("event_log_durable") is False:
                ops_table.add_row("event log", "[yellow]memory (amnesiac)[/]")
            console.print(ops_table)
            for key in ("event_log_note", "server_profile_hint"):
                note = ops.get(key)
                if note:
                    console.print(f"[dim]{note}[/]")

    if hasattr(host, "event_plane_status"):
        try:
            ep = host.event_plane_status()
        except Exception:
            ep = {}
        if ep:
            ep_table = Table(title="Event Plane", show_lines=True)
            ep_table.add_column("Surface", style="cyan")
            ep_table.add_column("Bus", style="green")
            ep_table.add_row("orchestration", str(ep.get("orchestration_bus", "—")))
            ep_table.add_row("internal inbound", str(ep.get("inbound_internal_bus", "—")))
            ep_table.add_row("work drain", str(ep.get("work_drain_bus", "—")))
            ep_table.add_row("journal", str(ep.get("journal_bus", "—")))
            ep_table.add_row(
                "internal bindings",
                str(ep.get("internal_inbound_bindings", 0)),
            )
            console.print(ep_table)
            note = ep.get("note")
            if note:
                console.print(f"[dim]{note}[/]")

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
