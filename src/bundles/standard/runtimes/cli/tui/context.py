"""
TUI context rendering — Rich markup for scopes, branches, and validation.
"""

from __future__ import annotations

from palm.common.job_inspection import format_step_context, inspect_job
from palm.core.orchestration import Job

__all__ = ["context_lines", "format_step_context"]


def context_lines(job: Job) -> list[str]:
    """Rich markup lines for panels and status tables."""
    ctx = inspect_job(job)
    lines: list[str] = []

    if ctx.scope_path:
        lines.append(f"[dim]Scope:[/] [cyan]{ctx.scope_path}[/]")
    if ctx.active_branch:
        lines.append(f"[dim]Branch:[/] [magenta]{ctx.active_branch}[/]")
    if ctx.branches:
        progress = ", ".join(
            f"[green]{branch.slug}✓[/]"
            if branch.completed
            else f"[bold magenta]{branch.slug}●[/]"
            if branch.active
            else f"[dim]{branch.slug}…[/]"
            for branch in ctx.branches
        )
        lines.append(f"[dim]Branches:[/] {progress}")
    if ctx.effective_schema_type:
        lines.append(f"[dim]Schema:[/] [blue]{ctx.effective_schema_type}[/]")
    if ctx.validation_error:
        lines.append(f"[dim]Validation:[/] [yellow]{ctx.validation_error}[/]")
    return lines
