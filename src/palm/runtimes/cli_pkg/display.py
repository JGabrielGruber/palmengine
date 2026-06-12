"""
Rich rendering for wizard prompts, jobs, and process instances.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import Job, JobStatus
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.pattern import WizardPattern
from palm.runtimes.cli_pkg.instance_ops import short_instance_id, status_emoji

_TERMINAL = frozenset({JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED})


def instance_id_for_job(job: Job) -> str:
    raw = job.metadata.get("instance_id")
    return str(raw) if raw else job.id


def wizard_prompt_bundle(job: Job) -> dict[str, Any] | None:
    raw = job.state.get(WizardKeys.ACTIVE_PROMPT)
    return dict(raw) if isinstance(raw, dict) else None


def wizard_scope_label(job: Job) -> str | None:
    """Return a compact scope label for prompts and status displays."""
    prompt = wizard_prompt_bundle(job)
    if prompt:
        current = prompt.get("current_scope")
        if isinstance(current, str) and current:
            return current
        stack = prompt.get("scope_stack")
        if isinstance(stack, list) and stack:
            return " › ".join(str(item) for item in stack)
    scope = job.state.current_scope()
    return str(scope) if scope is not None else None


def wizard_validation_hint(job: Job) -> str | None:
    """Return the primary validation message when the wizard is retrying input."""
    prompt = wizard_prompt_bundle(job)
    if prompt:
        error = prompt.get("validation_error")
        if isinstance(error, str) and error:
            return error
    error = job.state.get(WizardKeys.VALIDATION_ERROR)
    return str(error) if error is not None else None


def wizard_context_lines(job: Job) -> list[str]:
    """Build dim context lines for scope and validation (CLI panels)."""
    lines: list[str] = []
    scope = wizard_scope_label(job)
    if scope:
        lines.append(f"[dim]Scope:[/] [cyan]{scope}[/]")
    validation = wizard_validation_hint(job)
    if validation:
        lines.append(f"[dim]Validation:[/] [yellow]{validation}[/]")
    return lines


def render_wizard_panel(
    console: Any,
    job: Job,
    *,
    instance_id: str | None = None,
) -> None:
    from rich.panel import Panel

    iid = instance_id or instance_id_for_job(job)
    prompt = wizard_prompt_bundle(job)
    executable = job.executable
    wizard_name = executable.name if isinstance(executable, WizardPattern) else "wizard"

    if prompt:
        slug = prompt.get("slug", "?")
        title = prompt.get("title", slug)
        field_type = prompt.get("field_type", "text")
        body = f"[bold]{prompt.get('prompt', '')}[/]\n"
        choices = prompt.get("choices") or []
        if choices:
            body += "\n[bold]Choices:[/]\n"
            for choice in choices:
                body += f"  • [green]{choice}[/]\n"
        if field_type == "confirm":
            body += (
                "\n[yellow]→[/] Type [bold green]yes[/] or [bold green]confirm[/] to continue.\n"
            )
        answers = job.state.get(WizardKeys.ANSWERS)
        if isinstance(answers, dict) and answers:
            body += "\n[dim]Collected:[/]\n"
            for key, value in list(answers.items())[:8]:
                body += f"  {key}: [white]{value}[/]\n"
        for line in wizard_context_lines(job):
            body += f"\n{line}"
        panel = Panel(
            body.strip(),
            title=f"[bold]{wizard_name}[/] — [cyan]{title}[/] ({field_type})",
            subtitle=f"instance {iid[:12]}…  |  job {job.status.value}",
            border_style="blue",
        )
        console.print(panel)
        return

    if job.status in _TERMINAL:
        answers = {}
        if isinstance(job.executable, WizardPattern):
            answers = job.executable.answers(job.state)
        style = "green" if job.status == JobStatus.SUCCEEDED else "red"
        label = "completed" if job.status == JobStatus.SUCCEEDED else job.status.value
        console.print(
            Panel(
                f"[bold {style}]Wizard {label}[/]\n\nAnswers: {answers}",
                border_style=style,
            )
        )
        return

    console.print(f"[dim]Job {job.id[:12]}… status={job.status.value} (no active prompt)[/]")


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
    table.add_column("Step")
    table.add_column("Job", style="dim", overflow="fold")
    if show_snapshots:
        table.add_column("Snaps", justify="right", style="dim")

    for inst in instances:
        emoji = status_emoji(inst.status)
        row = [
            short_instance_id(inst.instance_id),
            inst.instance_id,
            inst.process_name or "—",
            inst.flow_name or "—",
            f"{emoji} {inst.status}",
            inst.wizard_step_slug or "—",
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
            "[dim]Tip:[/] use short ID prefix with "
            "[cyan]status <id>[/], [cyan]instance snapshots <id>[/], or [cyan]instance resume <id>[/]"
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
        for flow in flows:
            schema = "flow" if flow.has_state_schema else "—"
            ft.add_row(flow.name, flow.definition_id, flow.pattern, schema)
        console.print(ft)

    if not flows and not processes:
        console.print("[yellow]No definitions registered.[/]")


def render_job_status(console: Any, job: Job, instance_id: str) -> None:
    from rich.table import Table

    table = Table(title=f"Status — {instance_id[:16]}", show_header=False)
    table.add_row("instance_id", instance_id)
    table.add_row("job_id", job.id)
    table.add_row("status", job.status.value)
    if isinstance(job.executable, WizardPattern):
        table.add_row("current_step", job.executable.current_step_slug(job.state) or "—")
        table.add_row("answers", str(job.executable.answers(job.state)))
    scope = wizard_scope_label(job)
    if scope:
        table.add_row("scope", scope)
    validation = wizard_validation_hint(job)
    if validation:
        table.add_row("validation_error", validation)
    effective = job.state.effective_schema()
    if effective is not None and effective.definition:
        schema_type = effective.definition.get("type", "object")
        table.add_row("effective_schema", str(schema_type))
    prompt = wizard_prompt_bundle(job)
    if prompt:
        table.add_row("prompt", str(prompt.get("prompt", "")))
        table.add_row("field_type", str(prompt.get("field_type", "")))
    console.print(table)
    if job.status == JobStatus.WAITING_FOR_INPUT:
        render_wizard_panel(console, job, instance_id=instance_id)
