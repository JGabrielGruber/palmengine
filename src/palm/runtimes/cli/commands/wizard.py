"""Wizard shortcut commands — prefer ``flow start`` for new flows."""

from __future__ import annotations

from palm.runtimes.cli.commands.diagnostics import cmd_status
from palm.runtimes.cli.commands.input import cmd_input
from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.tui import actions as tui_actions


def cmd_wizard_list(ctx: CliContext, _args: list[str]) -> int:
    from rich.table import Table

    flows = [flow for flow in ctx.app.list_flows() if flow.pattern == "wizard"]
    if not flows:
        ctx.console.print("[yellow]No wizard flows registered.[/]")
        return 0

    table = Table(title="Wizard Flows", show_lines=True)
    table.add_column("Name", style="green")
    table.add_column("ID", style="cyan")
    table.add_column("Pattern")
    for flow in flows:
        table.add_row(flow.name, flow.definition_id, flow.pattern)
    ctx.console.print(table)
    return 0


def cmd_wizard_start(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] wizard start <flow_name_or_id>")
        return 1
    try:
        tui_actions.start_flow(ctx, args[0], via_shortcut="wizard")
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0


def cmd_wizard_status(ctx: CliContext, args: list[str]) -> int:
    return cmd_status(ctx, args)


def cmd_wizard_input(ctx: CliContext, args: list[str]) -> int:
    return cmd_input(ctx, args)
