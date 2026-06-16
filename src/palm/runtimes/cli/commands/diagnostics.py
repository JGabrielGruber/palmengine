"""
Host diagnostics — status dashboard, doctor report, and per-instance detail.

All read paths use ApplicationHost CQRS queries and projections.
"""

from __future__ import annotations

from palm import __version__
from palm.core.registry import pattern_registry, storage_registry
from palm.runtimes.cli.commands.dashboard import render_status_dashboard
from palm.runtimes.cli.commands.doctor import run_doctor
from palm.runtimes.cli.commands.views import render_job_status
from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.shared.output import emit_json
from palm.runtimes.cli.shared.runtime_display import format_runtime_line
from palm.runtimes.cli.tui import actions as tui_actions


def cmd_status(ctx: CliContext, args: list[str]) -> int:
    """
    Status command — projection dashboard by default.

    Modes:
      (none)           Live dashboard
      --dashboard      Dashboard (explicit)
      --brief          Compact engine summary
      --full           Full doctor report
      <instance_ref>   Instance job + wizard detail (CQRS read models)
    """
    if not args:
        return render_status_dashboard(ctx)
    flag = args[0]
    if flag == "--dashboard":
        return render_status_dashboard(ctx)
    if flag == "--brief":
        return run_engine_brief(ctx)
    if flag == "--full":
        return run_doctor(ctx)
    return _render_instance_status(ctx, flag)


def cmd_doctor(ctx: CliContext, args: list[str]) -> int:
    """Doctor command — full health report, or dashboard with ``--dashboard``."""
    if args and args[0] == "--dashboard":
        return render_status_dashboard(ctx)
    return run_doctor(ctx)


def run_engine_brief(ctx: CliContext) -> int:
    """Compact engine summary panel."""
    from rich.panel import Panel

    ctx.console.print(
        Panel(
            f"[bold]Palm Engine v{__version__}[/]\n"
            f"Host: {format_runtime_line(ctx.host)}\n"
            f"Patterns: {', '.join(pattern_registry.names())}\n"
            f"Storage:  {', '.join(storage_registry.names())}\n\n"
            f"[dim]Tip:[/] [cyan]status[/] live dashboard · "
            f"[cyan]status <id>[/] instance · "
            f"[cyan]doctor[/] full health",
            title="Status",
            border_style="green",
        )
    )
    return 0


def _render_instance_status(ctx: CliContext, ref: str) -> int:
    try:
        instance_id = tui_actions.resolve_instance_ref(ctx, ref)
    except (ValueError, Exception) as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1

    view = ctx.get_instance_status_view(instance_id)
    job = ctx.job_for_instance(instance_id)
    if ctx.output_format == "json":
        from palm.runtimes.cli.shared.job_inspect import inspect_job_json

        payload: dict[str, object] = {
            "instance_id": instance_id,
            "job_id": job.id,
            "status": job.status.value,
            **inspect_job_json(job),
        }
        if view is not None:
            payload["read_model"] = view.to_dict()
            progress = ctx.host.get_wizard_progress(instance_id=instance_id)
            if progress is not None:
                payload["wizard_progress"] = progress.to_dict()
        emit_json(ctx.console, payload)
        return 0

    render_job_status(ctx.console, job, instance_id)
    return 0