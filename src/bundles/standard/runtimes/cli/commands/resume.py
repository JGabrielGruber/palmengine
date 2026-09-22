"""Resume command — reload a persisted instance via ApplicationHost."""

from __future__ import annotations

from bundles.standard.runtimes.cli.shared.admission_voice import print_cli_error
from bundles.standard.runtimes.cli.shared.context import CliContext
from bundles.standard.runtimes.cli.tui import actions as tui_actions


def cmd_resume(ctx: CliContext, args: list[str]) -> int:
    """Resume a persisted process instance (``instance resume``)."""
    if not args:
        ctx.console.print("[red]Usage:[/] instance resume <instance_id>")
        return 1
    try:
        instance_id = ctx.resolve_instance_id(args[0])
        tui_actions.resume_instance(ctx, instance_id)
    except Exception as exc:
        print_cli_error(ctx.console, exc)
        return 1
    return 0
