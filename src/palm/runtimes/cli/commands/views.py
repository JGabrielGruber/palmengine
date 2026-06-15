"""
Command-mode views — compact tables and catalogs for one-shot CLI use.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import Job, JobStatus
from palm.runtimes.cli.shared.flow_labels import flow_detail_label
from palm.runtimes.cli.shared.instance_ops import short_instance_id, status_emoji
from palm.runtimes.cli.shared.job_inspect import format_step_context, inspect_job
from palm.runtimes.cli.tui.display import render_job_panel


def render_instance_table(console: Any, instances: list[Any], *, hint: str | None = None) -> None:
    from rich.table import Table

    if not instances:
        console.print("[dim]No process instances.[/]")
        return

    show_snapshots = any(getattr(inst, "snapshot_count", 0) for inst in instances)

    table = Table(title="Process Instances", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Full Instance ID", style="dim", overflow="fold")
    table.add_column("Process")
    table.add_column("Flow")
    table.add_column("Status", style="yellow")
    table.add_column("Step / Context")
    table.add_column("Job", style="dim", overflow="fold")
    if show_snapshots:
        table.add_column("Snaps", justify="right", style="dim")

    for inst in instances:
        emoji = status_emoji(inst.status)
        context = format_step_context(inst.wizard_step_slug)
        row = [
            short_instance_id(inst.instance_id),
            inst.instance_id,
            inst.process_name or "—",
            inst.flow_name or "—",
            f"{emoji} {inst.status}",
            context,
            inst.job_id,
        ]
        if show_snapshots:
            row.append(str(getattr(inst, "snapshot_count", 0)))
        table.add_row(*row)
    console.print(table)
    if hint:
        console.print(f"[dim]{hint}[/]")
    else:
        console.print(
            "[dim]Tip:[/] use [cyan]status <id>[/] for scope/branch detail, "
            "[cyan]instance resume <id>[/] to continue"
        )


def render_definition_catalog(ctx: Any) -> None:
    from rich.table import Table

    console = ctx.console
    flows = ctx.app.list_flows()
    processes = ctx.app.list_processes()

    if processes:
        pt = Table(title="Process Definitions", show_lines=True)
        pt.add_column("Name", style="green")
        pt.add_column("ID", style="cyan")
        pt.add_column("Flows", justify="right")
        for proc in processes:
            pt.add_row(
                proc.name,
                proc.definition_id,
                str(len(proc.flows)),
            )
        console.print(pt)

    if flows:
        ft = Table(title="Flow Definitions", show_lines=True)
        ft.add_column("Name", style="green")
        ft.add_column("ID", style="cyan")
        ft.add_column("Pattern")
        ft.add_column("Schema", style="dim")
        ft.add_column("Detail", style="dim")
        for flow in flows:
            schema = "flow" if flow.has_state_schema else "—"
            ft.add_row(flow.name, flow.definition_id, flow.pattern, schema, flow_detail_label(flow))
        console.print(ft)

    if not flows and not processes:
        console.print("[yellow]No definitions registered.[/]")


def render_job_status(console: Any, job: Job, instance_id: str) -> None:
    from rich.table import Table

    ctx = inspect_job(job)
    table = Table(title=f"Status — {instance_id[:16]}", show_header=False)
    table.add_row("instance_id", instance_id)
    table.add_row("job_id", job.id)
    table.add_row("status", job.status.value)
    table.add_row("pattern", ctx.pattern)
    if ctx.step:
        table.add_row("current_step", ctx.step)
    if ctx.active_branch:
        table.add_row("active_branch", ctx.active_branch)
    if ctx.scope_path:
        table.add_row("scope", ctx.scope_path)
    if ctx.branch_progress:
        table.add_row("branch_progress", ctx.branch_progress)
    if ctx.branches:
        branch_summary = ", ".join(
            f"{branch.slug}{'✓' if branch.completed else '●' if branch.active else '…'}"
            for branch in ctx.branches
        )
        table.add_row("branches", branch_summary)
    if ctx.answers_preview:
        table.add_row("answers", str(ctx.answers_preview))
    if ctx.merged_preview:
        table.add_row("merged", str(ctx.merged_preview))
    if ctx.validation_error:
        table.add_row("validation_error", ctx.validation_error)
    if ctx.effective_schema_type:
        table.add_row("effective_schema", ctx.effective_schema_type)
    if ctx.prompt:
        table.add_row("prompt", ctx.prompt)
    if ctx.field_type:
        table.add_row("field_type", ctx.field_type)
    console.print(table)
    if job.status == JobStatus.WAITING_FOR_INPUT:
        render_job_panel(console, job, instance_id=instance_id)
