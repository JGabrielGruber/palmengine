"""
Shared CLI actions — submit, input, backtrack, resume (EmbeddedRuntime API).
"""

from __future__ import annotations

from palm.core.orchestration import Job, JobStatus
from palm.patterns.wizard.pattern import WizardPattern
from palm.runtimes.cli_pkg.context import CliContext
from palm.runtimes.cli_pkg.display import instance_id_for_job, render_wizard_panel


def submit_process(ctx: CliContext, ref: str) -> Job:
    job = ctx.runtime.submit_process(ref)
    if isinstance(job, list):
        job = job[0]
    iid = instance_id_for_job(job)
    ctx.set_active(iid, job.id)
    render_wizard_panel(ctx.console, job, instance_id=iid)
    return job


def submit_flow(ctx: CliContext, ref: str) -> Job:
    job = ctx.runtime.submit_flow(ref)
    iid = instance_id_for_job(job)
    ctx.set_active(iid, job.id)
    render_wizard_panel(ctx.console, job, instance_id=iid)
    return job


def resume_instance(ctx: CliContext, instance_id: str) -> Job:
    job = ctx.runtime.resume_process(instance_id)
    ctx.set_active(instance_id, job.id)
    render_wizard_panel(ctx.console, job, instance_id=instance_id)
    return job


def provide_input(ctx: CliContext, instance_id: str, value: str) -> str | None:
    job_id = ctx.resolve_job_id(instance_id)
    slug = ctx.runtime.provide_input(job_id, value)
    job = ctx.runtime.get_job(job_id)
    iid = instance_id_for_job(job)
    ctx.set_active(iid, job_id)
    render_wizard_panel(ctx.console, job, instance_id=iid)
    if job.status in (JobStatus.SUCCEEDED, JobStatus.FAILED, JobStatus.CANCELLED):
        ctx.active_instance_id = None
    return slug


def backtrack(ctx: CliContext, instance_id: str, to_slug: str) -> None:
    job = ctx.job_for_instance(instance_id)
    wizard = job.executable
    if not isinstance(wizard, WizardPattern):
        raise TypeError(f"Instance {instance_id!r} is not a wizard job")
    wizard.request_backtrack(job.state, to_slug)
    ctx.runtime.orchestration.resume_job(job.id)
    ctx.runtime.executor.persist_job(job)
    job = ctx.runtime.get_job(job.id)
    render_wizard_panel(ctx.console, job, instance_id=instance_id)
    ctx.console.print(f"[green]Backtracked to[/] [bold]{to_slug}[/]")


def resolve_instance_ref(ctx: CliContext, ref: str | None) -> str:
    if ref:
        inst = ctx.get_instance(ref)
        return inst.instance_id
    if ctx.active_instance_id:
        return ctx.active_instance_id
    raise ValueError("No instance id provided and no active instance")
