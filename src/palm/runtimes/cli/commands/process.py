"""Process commands — definition catalog, submit, resume."""

from __future__ import annotations

from palm.runtimes.cli.commands.views import render_definition_catalog
from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.tui import actions as tui_actions


def cmd_process_list(ctx: CliContext, _args: list[str]) -> int:
    render_definition_catalog(ctx)
    return 0


def cmd_process_submit(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] process submit <process-name-or-id>")
        return 1
    try:
        ctx.app.resolve_process(args[0])
        tui_actions.submit_process(ctx, args[0])
        ctx.console.print("[dim]Process submitted.[/]")
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0


def cmd_process_resume(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] process resume <instance_id>")
        return 1
    try:
        instance_id = ctx.resolve_instance_id(args[0])
        tui_actions.resume_instance(ctx, instance_id)
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0