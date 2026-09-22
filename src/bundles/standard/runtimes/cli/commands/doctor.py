"""
CLI doctor — render InspectService.doctor. One bag with REST / assist / MCP.

Operator extras (instance list, definition catalog) stay as CQRS present.
Anatomy, admission pointer, neonroot, and CS-002 packaging come from inspect.
"""

from __future__ import annotations

from typing import Any

from palm.common.job_inspection import inspect_job
from bundles.standard.runtimes.cli.commands.views import render_definition_catalog, render_instance_table
from bundles.standard.runtimes.cli.shared.context import CliContext
from bundles.standard.runtimes.cli.shared.instance_ops import is_terminal_status
from bundles.standard.runtimes.cli.shared.output import emit_json
from bundles.standard.runtimes.cli.shared.runtime_display import format_runtime_line
from bundles.standard.runtimes.cli.shared.settings import is_durable_storage
from bundles.standard.runtimes.cli.shared.startup import format_persistence_notice
from bundles.standard.runtimes.cli.tui.context import context_lines
from palm.services.inspect.present import DOCTOR_KIND


def run_doctor(ctx: CliContext) -> int:
    """Print the inspect doctor bag; return 0 when the report is healthy."""
    inspect = getattr(ctx.host, "inspect", None)
    if inspect is None:
        ctx.console.print("[red]host.inspect not available[/]")
        return 1
    try:
        runtime = ctx.host.runtime()
    except Exception as exc:
        ctx.console.print(f"[red]runtime not ready:[/] {exc}")
        return 1

    report = inspect.doctor(runtime)
    if ctx.output_format == "json":
        emit_json(ctx.console, report)
        return 0 if report.get("status") == "ok" else 1
    return _render_human(ctx, report)


def _render_human(ctx: CliContext, report: dict[str, Any]) -> int:
    from rich.panel import Panel
    from rich.table import Table

    console = ctx.console
    host = ctx.host
    issues = [str(i) for i in (report.get("issues") or [])]
    if not ctx.is_runtime_started():
        issues.append("ApplicationHost runtimes are not started")

    storage = report.get("storage") if isinstance(report.get("storage"), dict) else {}
    backend_name = str(storage.get("backend") or "(none)")
    backend_open = bool(storage.get("open"))
    persistence_style = "green" if is_durable_storage(backend_name) else "yellow"
    border = "green" if not issues else "yellow"

    console.print(
        Panel(
            f"[bold]Palm Engine v{report.get('version') or ''}[/]\n"
            f"Runtime: {format_runtime_line(host)}\n"
            f"Host roles: {', '.join(sorted(host.profile.roles))}\n"
            f"Storage: {backend_name} — "
            f"{'[green]ready[/]' if backend_open else '[red]unavailable[/]'}\n"
            f"[dim]kind={report.get('kind', DOCTOR_KIND)}  "
            f"eyes={report.get('eyes_law') or '—'}[/]",
            title="Engine Health",
            border_style=border,
        )
    )
    console.print(
        Panel(
            format_persistence_notice(ctx.app),
            title="Persistence",
            border_style=persistence_style,
        )
    )

    registries = report.get("registries") if isinstance(report.get("registries"), dict) else {}
    if registries:
        reg_table = Table(title="Registered Plugins", show_lines=True)
        reg_table.add_column("Registry", style="cyan")
        reg_table.add_column("Names")
        for name, values in registries.items():
            if isinstance(values, list | tuple):
                shown = ", ".join(str(v) for v in values) or "—"
            else:
                shown = str(values)
            reg_table.add_row(str(name), shown)
        console.print(reg_table)

    _render_transform_catalog(console, registries.get("transforms") or [])

    resource_count = report.get("resource_count")
    jobs = report.get("jobs") if isinstance(report.get("jobs"), dict) else {}
    inst_table = Table(title="Catalog & Persistence", show_lines=True)
    inst_table.add_column("Resource", style="cyan")
    inst_table.add_column("Count", justify="right")
    inst_table.add_column("Notes")
    flows = ctx.app.list_flows()
    processes = ctx.app.list_processes()
    resources = ctx.app.list_resources()
    schema_flows = sum(1 for flow in flows if flow.has_state_schema)
    schema_resources = sum(1 for item in resources if item.has_schemas)
    schema_note = f"{schema_flows} with state_schema" if schema_flows else "none with state_schema"
    inst_table.add_row("flow definitions", str(len(flows)), f"in-memory + storage ({schema_note})")
    inst_table.add_row("process definitions", str(len(processes)), "")
    resource_note = (
        f"{schema_resources} with input/output schema"
        if schema_resources
        else f"inspect resource_count={resource_count}"
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
    if jobs:
        inst_table.add_row(
            "jobs (inspect)",
            str(jobs.get("total") or 0),
            f"waiting={jobs.get('waiting_for_input') or 0}",
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

    _render_structure(console, report)
    _render_control_plane(console, report)
    _render_neonroot(console, report)

    note = report.get("note")
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


def _render_transform_catalog(console: Any, names: Any) -> None:
    from rich.table import Table

    from palm.common.transforms.catalog import TRANSFORM_CATALOG

    transform_names = [str(n) for n in names] if isinstance(names, list | tuple) else []
    if not transform_names:
        return
    tx_table = Table(title="Transform Rules", show_lines=True)
    tx_table.add_column("Rule", style="cyan", no_wrap=True)
    tx_table.add_column("Description")
    for name in transform_names:
        tx_table.add_row(name, TRANSFORM_CATALOG.get(name, "Registered transform rule"))
    console.print(tx_table)


def _render_structure(console: Any, report: dict[str, Any]) -> None:
    from rich.table import Table

    cp = report.get("control_plane") if isinstance(report.get("control_plane"), dict) else {}
    structure = cp.get("structure") if isinstance(cp.get("structure"), dict) else {}
    top = report.get("top") if isinstance(report.get("top"), dict) else {}
    if not structure and not top:
        return

    may = structure.get("may_run_business")
    may_style = "green" if may else "yellow"
    table = Table(title="Structure admission", show_lines=True)
    table.add_column("Item", style="cyan")
    table.add_column("Value")
    table.add_row(
        "may_run_business",
        f"[{may_style}]{may}[/]" if may is not None else "[dim]unknown[/]",
    )
    table.add_row("phase", str(structure.get("phase") or "—"))
    table.add_row("definition_id", str(structure.get("definition_id") or "—"))
    caps = structure.get("capabilities") or []
    table.add_row(
        "capabilities",
        ", ".join(str(c) for c in caps) if caps else "—",
    )
    table.add_row("gated paths", str(structure.get("gated_count", "—")))
    table.add_row("paid edges", str(structure.get("paid_edge_count", "—")))
    open_n = int(structure.get("open_residual_count") or 0)
    table.add_row(
        "open residuals (named)",
        f"[yellow]{open_n}[/]" if open_n else "[green]0[/]",
    )
    console.print(table)
    open_ids = structure.get("open_residual_ids") or []
    if open_ids:
        console.print(
            "[dim]Open named residuals (not dual readiness — exit map):[/] "
            + ", ".join(f"[yellow]{rid}[/]" for rid in open_ids)
        )
    if structure.get("note"):
        console.print(f"[dim]{structure['note']}[/]")


def _render_control_plane(console: Any, report: dict[str, Any]) -> None:
    from rich.table import Table

    cp = report.get("control_plane") if isinstance(report.get("control_plane"), dict) else {}
    if not cp:
        return
    console.print("[dim]Host ops / event-plane tables below are packaging residual (CS-002).[/]")
    ops = cp.get("ops") if isinstance(cp.get("ops"), dict) else {}
    if ops:
        ops_table = Table(title="Ops (packaging residual)", show_lines=True)
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
        plane_running = cp.get("start_plane_running")
        if plane_running is not None:
            ops_table.add_row("start_plane_running", str(plane_running))
        console.print(ops_table)
        for key in ("event_log_note", "server_profile_hint"):
            note = ops.get(key)
            if note:
                console.print(f"[dim]{note}[/]")

    ep = cp.get("event_plane") if isinstance(cp.get("event_plane"), dict) else {}
    if ep:
        ep_table = Table(title="Event Plane (packaging residual)", show_lines=True)
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


def _render_neonroot(console: Any, report: dict[str, Any]) -> None:
    from rich.table import Table

    workloads = report.get("workloads") if isinstance(report.get("workloads"), dict) else {}
    registered = "neonroot" in {str(n) for n in (workloads.get("registered_runtimes") or [])}
    row = None
    for item in workloads.get("runtimes") or []:
        if isinstance(item, dict) and item.get("name") == "neonroot":
            row = item
            break
    if not registered and row is None:
        return
    health = (
        row.get("health") if isinstance(row, dict) and isinstance(row.get("health"), dict) else {}
    )
    detail = health.get("detail") if isinstance(health.get("detail"), dict) else {}
    available = health.get("available")
    if available is True:
        cli = f"[green]yes[/] {detail.get('version') or detail.get('path') or ''}"
    elif available is False:
        cli = f"[yellow]no[/] {detail.get('error') or health.get('message') or ''}"
    else:
        cli = "—"
    table = Table(title="NeonRoot (WorkloadRuntime)", show_lines=True)
    table.add_column("Item", style="cyan")
    table.add_column("Value")
    table.add_row(
        "runtime registered",
        "[green]yes[/]" if registered else "[red]no[/]",
    )
    table.add_row("CLI available", cli.strip())
    console.print(table)


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
