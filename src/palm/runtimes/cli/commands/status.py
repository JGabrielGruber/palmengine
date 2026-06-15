"""Status commands — engine summary and per-instance job detail."""

from __future__ import annotations

from palm import __version__
from palm.core.registry import pattern_registry, storage_registry
from palm.runtimes.cli.commands.doctor import run_doctor
from palm.runtimes.cli.commands.views import render_job_status
from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.shared.output import emit_json
from palm.runtimes.cli.tui import actions as tui_actions


def cmd_status(ctx: CliContext, args: list[str]) -> int:
    if args and args[0] == "--full":
        return run_doctor(ctx)
    if not args and not ctx.active_instance_id:
        return cmd_engine_status(ctx)
    try:
        ref = args[0] if args else None
        iid = tui_actions.resolve_instance_ref(ctx, ref)
    except (ValueError, Exception) as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    job = ctx.job_for_instance(iid)
    if ctx.output_format == "json":
        from palm.runtimes.cli.shared.job_inspect import inspect_job_json

        payload: dict[str, object] = {
            "instance_id": iid,
            "job_id": job.id,
            "status": job.status.value,
            **inspect_job_json(job),
        }
        emit_json(ctx.console, payload)
        return 0
    render_job_status(ctx.console, job, iid)
    return 0


def cmd_engine_status(ctx: CliContext) -> int:
    from rich.panel import Panel

    ctx.console.print(
        Panel(
            f"[bold]Palm Engine v{__version__}[/]\n"
            f"Runtime: embedded — "
            f"{'[green]started[/]' if ctx.app.is_runtime_started() else '[red]stopped[/]'}\n"
            f"Patterns: {', '.join(pattern_registry.names())}\n"
            f"Storage:  {', '.join(storage_registry.names())}\n\n"
            f"[dim]Tip:[/] [cyan]flow start <name>[/] to run a flow, "
            f"[cyan]doctor[/] for health, [cyan]status <id>[/] for detail",
            title="Status",
            border_style="green",
        )
    )
    return 0
