"""
Shared CLI actions — thin wrappers over :class:`~palm.app.app.PalmApp`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.core.orchestration import Job, JobStatus
from palm.patterns.wizard.pattern import WizardPattern
from palm.runtimes.cli_pkg.context import CliContext
from palm.runtimes.cli_pkg.display import (
    flow_start_hint,
    instance_id_for_job,
    render_job_panel,
)
from palm.runtimes.cli_pkg.job_context import inspect_job

if TYPE_CHECKING:
    from palm.definitions.flow import FlowDefinition


def submit_process(ctx: CliContext, ref: str) -> Job:
    job = ctx.app.submit_process(ref)
    if isinstance(job, list):
        job = job[0]
    iid = instance_id_for_job(job)
    ctx.set_active(iid, job.id)
    render_job_panel(ctx.console, job, instance_id=iid)
    return job


def submit_flow(ctx: CliContext, ref: str) -> Job:
    """Submit a flow without resolve/feedback (used by internal callers)."""
    job = ctx.app.submit_flow(ref)
    iid = instance_id_for_job(job)
    ctx.set_active(iid, job.id)
    render_job_panel(ctx.console, job, instance_id=iid)
    return job


def start_flow(
    ctx: CliContext,
    ref: str,
    *,
    via_shortcut: str | None = None,
) -> Job:
    """
    Resolve and start any registered flow with pattern-aware feedback.

    ``via_shortcut`` is set when invoked through a legacy alias (e.g. ``wizard start``).
    """
    flow = ctx.app.resolve_flow(ref)
    if via_shortcut == "wizard" and flow.pattern != "wizard":
        ctx.console.print(
            f"[dim]Note:[/] {flow.name!r} is a [cyan]{flow.pattern}[/] flow — "
            f"prefer [cyan]flow start {flow.name}[/] or [cyan]start {flow.name}[/]."
        )
    job = ctx.app.submit_flow(ref)
    iid = instance_id_for_job(job)
    ctx.set_active(iid, job.id)
    _print_flow_started(ctx, flow)
    render_job_panel(ctx.console, job, instance_id=iid)
    return job


def _print_flow_started(ctx: CliContext, flow: FlowDefinition) -> None:
    hint = flow_start_hint(flow)
    if flow.pattern == "parallel":
        ctx.console.print(
            "[dim]Parallel flow started[/]"
            + (f" — {hint}" if hint else "")
            + ". Branches interleave input; watch for "
            "[magenta]@parallel:<branch>[/] in the REPL prompt."
        )
        return
    if flow.pattern == "wizard":
        ctx.console.print("[dim]Wizard started.[/]")
        return
    label = f"{flow.pattern} flow started"
    ctx.console.print(f"[dim]{label}[/]" + (f" — {hint}" if hint else "") + ".")


def resume_instance(ctx: CliContext, instance_id: str) -> Job:
    job = ctx.app.resume_process(instance_id)
    ctx.set_active(instance_id, job.id)
    render_job_panel(ctx.console, job, instance_id=instance_id)
    return job


def provide_input(ctx: CliContext, instance_id: str, value: str) -> str | None:
    job_id = ctx.resolve_job_id(instance_id)
    before = inspect_job(ctx.app.get_job(job_id))
    slug = ctx.app.provide_input(job_id, value)
    job = ctx.app.get_job(job_id)
    iid = instance_id_for_job(job)
    ctx.set_active(iid, job_id)
    if before.active_branch:
        ctx.console.print(
            f"[dim]→[/] input for branch [magenta]{before.active_branch}[/]"
            + (f" (step {slug})" if slug else ""),
        )
    render_job_panel(ctx.console, job, instance_id=iid)
    if job.status in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED):
        ctx.active_instance_id = None
    return slug


def backtrack(ctx: CliContext, instance_id: str, to_slug: str) -> None:
    job = ctx.job_for_instance(instance_id)
    wizard = job.executable
    if not isinstance(wizard, WizardPattern):
        raise TypeError(f"Instance {instance_id!r} is not a wizard job")
    wizard.request_backtrack(job.state, to_slug)
    ctx.app.resume_job(job.id)
    ctx.app.persist_job(job)
    job = ctx.app.get_job(job.id)
    render_job_panel(ctx.console, job, instance_id=instance_id)
    ctx.console.print(f"[green]Backtracked to[/] [bold]{to_slug}[/]")


def resolve_instance_ref(ctx: CliContext, ref: str | None) -> str:
    if ref:
        return ctx.resolve_instance_id(ref)
    if ctx.active_instance_id:
        return ctx.active_instance_id
    raise ValueError("No instance id provided and no active instance")
