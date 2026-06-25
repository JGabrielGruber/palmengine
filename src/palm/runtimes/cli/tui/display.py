"""
TUI display — Rich panels for interactive wizard and parallel prompts.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import Job, JobStatus
from palm.patterns.parallel.pattern import ParallelPattern
from palm.patterns.wizard.pattern import WizardPattern
from palm.runtimes.cli.shared.job_inspect import inspect_job
from palm.runtimes.cli.tui.context import context_lines

_TERMINAL = frozenset({JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED})


def render_job_panel(
    console: Any,
    job: Job,
    *,
    instance_id: str | None = None,
) -> None:
    """Render an interactive or terminal panel for any input-capable pattern."""
    from rich.panel import Panel

    from palm.runtimes.cli.shared.job_inspect import instance_id_for_job

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
        if ctx.field_type == "transform":
            body += "\n[yellow]→[/] Transform step — runs automatically when reached.\n"
            if ctx.transform_rule:
                body += f"[dim]Rule:[/] [cyan]{ctx.transform_rule}[/]\n"
            if ctx.transform_source_key and ctx.transform_target_key:
                body += (
                    f"[dim]Keys:[/] {ctx.transform_source_key} "
                    f"[dim]→[/] {ctx.transform_target_key}\n"
                )
            if ctx.transform_source_preview:
                body += f"[dim]Input preview:[/] {ctx.transform_source_preview}\n"
        if ctx.field_type == "resource":
            if ctx.waiting_for_child:
                body += (
                    "\n[yellow]→[/] Waiting for nested wizard"
                    f" [dim](job {ctx.waiting_for_child_job_id})[/].\n"
                )
            else:
                body += "\n[yellow]→[/] Resource step — invokes automatically when reached.\n"
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
