"""
Rich rendering for wizard prompts, jobs, and process instances.
"""

from __future__ import annotations

from typing import Any

from palm.core.orchestration import Job, JobStatus
from palm.patterns.wizard.keys import WizardKeys
from palm.patterns.wizard.pattern import WizardPattern

_TERMINAL = frozenset({JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED})


def instance_id_for_job(job: Job) -> str:
    raw = job.metadata.get("instance_id")
    return str(raw) if raw else job.id


def wizard_prompt_bundle(job: Job) -> dict[str, Any] | None:
    raw = job.state.get(WizardKeys.ACTIVE_PROMPT)
    return dict(raw) if isinstance(raw, dict) else None


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


def render_instance_table(console: Any, instances: list[Any]) -> None:
    from rich.table import Table

    if not instances:
        console.print("[dim]No process instances.[/]")
        return

    table = Table(title="Process Instances", show_lines=True)
    table.add_column("Instance", style="cyan")
    table.add_column("Process")
    table.add_column("Flow")
    table.add_column("Status", style="yellow")
    table.add_column("Step")
    table.add_column("Job", style="dim")

    for inst in instances:
        table.add_row(
            inst.instance_id[:14],
            inst.process_name or "—",
            inst.flow_name or "—",
            inst.status,
            inst.wizard_step_slug or "—",
            inst.job_id[:14],
        )
    console.print(table)


def render_definition_catalog(ctx: Any) -> None:
    from rich.table import Table

    console = ctx.console
    repo = ctx.runtime.repository
    flows = repo.list_flows()
    processes = repo.list_processes()

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
        for flow in flows:
            ft.add_row(flow.name, flow.definition_id, flow.pattern)
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
    prompt = wizard_prompt_bundle(job)
    if prompt:
        table.add_row("prompt", str(prompt.get("prompt", "")))
        table.add_row("field_type", str(prompt.get("field_type", "")))
    console.print(table)
    if job.status == JobStatus.WAITING_FOR_INPUT:
        render_wizard_panel(console, job, instance_id=instance_id)
