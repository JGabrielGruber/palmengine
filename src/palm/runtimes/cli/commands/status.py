"""Status commands — dashboard, engine summary, and per-instance job detail."""

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
    if args and args[0] == "--full":
        return run_doctor(ctx)
    if args and args[0] == "--brief":
        return cmd_engine_status(ctx)
    if args and args[0] == "--dashboard":
        return render_status_dashboard(ctx)
    if not args and not ctx.active_instance_id:
        return render_status_dashboard(ctx)
    try:
        ref = args[0] if args else None
        iid = tui_actions.resolve_instance_ref(ctx, ref)
    except (ValueError, Exception) as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    view = ctx.get_instance_status_view(iid)
    job = ctx.job_for_instance(iid)
    if ctx.output_format == "json":
        from palm.runtimes.cli.shared.job_inspect import inspect_job_json

        payload: dict[str, object] = {
            "instance_id": iid,
            "job_id": job.id,
            "status": job.status.value,
            **inspect_job_json(job),
        }
        if view is not None:
            payload["read_model"] = view.to_dict()
            progress = ctx.host.get_wizard_progress(instance_id=iid)
            if progress is not None:
                payload["wizard_progress"] = progress.to_dict()
        emit_json(ctx.console, payload)
        return 0
    render_job_status(ctx.console, job, iid)
    return 0


def cmd_engine_status(ctx: CliContext) -> int:
    from rich.panel import Panel

    ctx.console.print(
        Panel(
            f"[bold]Palm Engine v{__version__}[/]\n"
            f"Runtime: {format_runtime_line(ctx.host)}\n"
            f"Patterns: {', '.join(pattern_registry.names())}\n"
            f"Storage:  {', '.join(storage_registry.names())}\n\n"
            f"[dim]Tip:[/] [cyan]status[/] shows the live dashboard, "
            f"[cyan]status <id>[/] for instance detail, "
            f"[cyan]status --full[/] for doctor",
            title="Status",
            border_style="green",
        )
    )
    return 0