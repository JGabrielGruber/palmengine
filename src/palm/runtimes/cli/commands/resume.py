"""Resume command — reload a persisted instance via ApplicationHost."""

from __future__ import annotations

from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.tui import actions as tui_actions


def cmd_resume(ctx: CliContext, args: list[str]) -> int:
    """Resume a persisted process instance (``instance resume`` / ``process resume``)."""
    if not args:
        ctx.console.print("[red]Usage:[/] instance resume <instance_id>")
        return 1
    try:
        instance_id = ctx.resolve_instance_id(args[0])
        tui_actions.resume_instance(ctx, instance_id)
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0