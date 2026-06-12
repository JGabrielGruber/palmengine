"""
Rich rendering for wizard prompts, jobs, and process instances.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import Job, JobStatus
from palm.patterns.parallel.pattern import ParallelPattern
from palm.patterns.wizard.pattern import WizardPattern
from palm.runtimes.cli_pkg.instance_ops import short_instance_id, status_emoji
from palm.runtimes.cli_pkg.job_context import context_lines, format_step_context, inspect_job

_TERMINAL = frozenset({JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED})


def instance_id_for_job(job: Job) -> str:
    raw = job.metadata.get("instance_id")
    return str(raw) if raw else job.id


def render_job_panel(
    console: Any,
    job: Job,
    *,
    instance_id: str | None = None,
) -> None:
    """Render an interactive or terminal panel for any input-capable pattern."""
    from rich.panel import Panel

    iid = instance_id or instance_id_for_job(job)
    ctx = inspect_job(job)
    executable = job.executable
    pattern_name = getattr(executable, "name", ctx.pattern)

    if ctx.prompt or (job.status == JobStatus.WAITING_FOR_INPUT and ctx.branches):
        body = ""
        if ctx.prompt:
            body = f"[bold]{ctx.prompt}[/]\n"
        if ctx.choices:
            body += "\n[bold]Options:[/] [dim](enter number or name)[/]\n"
            for index, choice in enumerate(ctx.choices, start=1):
                body += f"  [cyan]{index}.[/] [green]{choice}[/]\n"
        if ctx.collection_phase == "select_item" and ctx.collection_item_previews:
            body += "\n[bold]Items:[/] [dim](enter number, partial label, or 'cancel')[/]\n"
            for index, preview in enumerate(ctx.collection_item_previews, start=1):
                body += f"  [cyan]{index}.[/] [green]{preview}[/]\n"
        elif ctx.collection_items:
            body += "\n[bold]Current list:[/]\n"
            for index, item in enumerate(ctx.collection_items, start=1):
                title = item.get("title", f"Item {index}")
                priority = item.get("priority")
                due = item.get("due_date")
                line = f"  {index}. {title}"
                if priority:
                    line += f" [dim]({priority})[/]"
                if due:
                    line += f" [dim]due {due}[/]"
                body += line + "\n"
        if ctx.field_type == "confirm":
            body += (
                "\n[yellow]→[/] Type [bold green]yes[/] or [bold green]confirm[/] to continue.\n"
            )
        if ctx.active_branch:
            body += f"\n[dim]Input goes to branch[/] [magenta]{ctx.active_branch}[/]"
            if ctx.branch_progress:
                body += f" [dim]({ctx.branch_progress} branches complete)[/]"
            body += "\n"
        if ctx.answers_preview and ctx.pattern == "wizard":
            body += "\n[dim]Collected:[/]\n"
            for key, value in list(ctx.answers_preview.items())[:8]:
                body += f"  {key}: [white]{value}[/]\n"
        if ctx.answers_preview and ctx.pattern == "parallel":
            body += "\n[dim]Branch results:[/]\n"
            for key, value in list(ctx.answers_preview.items())[:8]:
                body += f"  {key}: [white]{value}[/]\n"
        for line in context_lines(job):
            body += f"\n{line}"

        title_slug = ctx.prompt_title or ctx.step or "?"
        field = ctx.field_type or "text"
        panel = Panel(
            body.strip() or "[dim]Waiting for input…[/]",
            title=f"[bold]{pattern_name}[/] — [cyan]{title_slug}[/] ({field})",
            subtitle=f"instance {iid[:12]}…  |  job {job.status.value}",
            border_style="magenta" if ctx.pattern == "parallel" else "blue",
        )
        console.print(panel)
        return

    if job.status in _TERMINAL:
        answers: dict[str, Any] = {}
        if isinstance(job.executable, WizardPattern | ParallelPattern):
            answers = job.executable.answers(job.state)
        style = "green" if job.status == JobStatus.SUCCEEDED else "red"
        label = "completed" if job.status == JobStatus.SUCCEEDED else job.status.value
        console.print(
            Panel(
                f"[bold {style}]{ctx.pattern.title()} {label}[/]\n\nResults: {answers}",
                border_style=style,
            )
        )
        return

    lines = context_lines(job)
    if lines:
        console.print(
            Panel(
                "\n".join(lines),
                title=f"[bold]{pattern_name}[/] — {job.status.value}",
                border_style="yellow",
            )
        )
        return

    console.print(f"[dim]Job {job.id[:12]}… status={job.status.value}[/]")


def render_wizard_panel(
    console: Any,
    job: Job,
    *,
    instance_id: str | None = None,
) -> None:
    """Backward-compatible alias for :func:`render_job_panel`."""
    render_job_panel(console, job, instance_id=instance_id)


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
        context = _instance_context_label(inst)
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


def _instance_context_label(inst: Any) -> str:
    return format_step_context(inst.wizard_step_slug)


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
            detail = _flow_detail_label(flow)
            ft.add_row(flow.name, flow.definition_id, flow.pattern, schema, detail)
        console.print(ft)

    if not flows and not processes:
        console.print("[yellow]No definitions registered.[/]")


def flow_detail_label(flow: Any) -> str:
    """Compact catalog/detail label for a flow definition."""
    return _flow_detail_label(flow)


def flow_start_hint(flow: Any) -> str | None:
    """Short operator hint shown when a flow starts."""
    detail = flow_detail_label(flow)
    return detail if detail != "—" else None


def _flow_detail_label(flow: Any) -> str:
    if flow.pattern == "parallel":
        branches = flow.options.get("branches") if isinstance(flow.options, dict) else None
        if isinstance(branches, list):
            slugs = [str(item.get("slug", "?")) for item in branches if isinstance(item, dict)]
            merge = flow.options.get("merge_strategy", "all")
            return f"{len(slugs)} branches ({merge}): {', '.join(slugs)}"
        return "parallel"
    if flow.pattern == "wizard" and isinstance(flow.options, dict):
        steps = flow.options.get("steps")
        if isinstance(steps, list):
            return f"{len(steps)} steps"
    return "—"


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
