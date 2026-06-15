"""Flow commands — list and start flows."""

from __future__ import annotations

from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.shared.flow_labels import flow_detail_label
from palm.runtimes.cli.tui import actions as tui_actions


def cmd_flow_list(ctx: CliContext, _args: list[str]) -> int:
    from rich.table import Table

    flows = ctx.app.list_flows()
    if not flows:
        ctx.console.print("[yellow]No flows registered.[/]")
        return 0

    table = Table(title="Registered Flows", show_lines=True)
    table.add_column("Name", style="green")
    table.add_column("ID", style="cyan")
    table.add_column("Pattern")
    table.add_column("Schema", style="dim")
    table.add_column("Detail", style="dim")
    for flow in flows:
        schema = "flow" if flow.has_state_schema else "—"
        table.add_row(flow.name, flow.definition_id, flow.pattern, schema, flow_detail_label(flow))
    ctx.console.print(table)
    ctx.console.print("[dim]Start any flow:[/] [cyan]flow start <name>[/] or [cyan]start <name>[/]")
    return 0


def cmd_flow_start(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] flow start <flow_name_or_id>")
        return 1
    try:
        tui_actions.start_flow(ctx, args[0])
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    return 0


def cmd_start(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] start <flow_name_or_id>  [dim](alias: flow start)[/]")
        return 1
    return cmd_flow_start(ctx, args)
