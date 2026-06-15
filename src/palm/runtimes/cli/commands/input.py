"""Input commands — provide values and backtrack wizard steps."""

from __future__ import annotations

from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.tui import actions as tui_actions


def cmd_input(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] input [<instance_id>] <value>")
        return 1

    if len(args) == 1 and ctx.active_instance_id:
        iid = ctx.active_instance_id
        value = args[0]
    elif len(args) >= 2:
        try:
            iid = tui_actions.resolve_instance_ref(ctx, args[0])
        except Exception as exc:
            ctx.console.print(f"[red]{exc}[/]")
            return 1
        value = " ".join(args[1:])
    else:
        ctx.console.print("[red]Usage:[/] input [<instance_id>] <value>")
        return 1

    try:
        tui_actions.provide_input(ctx, iid, value)
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0


def cmd_back(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] back [<instance_id>] <step_slug>")
        return 1

    if len(args) == 1 and ctx.active_instance_id:
        iid = ctx.active_instance_id
        target = args[0]
    elif len(args) >= 2:
        try:
            iid = tui_actions.resolve_instance_ref(ctx, args[0])
        except Exception as exc:
            ctx.console.print(f"[red]{exc}[/]")
            return 1
        target = args[1]
    else:
        ctx.console.print("[red]Usage:[/] back [<instance_id>] <step_slug>")
        return 1

    try:
        tui_actions.backtrack(ctx, iid, target)
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0
