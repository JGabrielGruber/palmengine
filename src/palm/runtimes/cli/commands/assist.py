"""Assist commands — conversational operator guidance in the CLI REPL."""

from __future__ import annotations

from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.tui.display import render_assistant_panel


def cmd_assist_list(ctx: CliContext, _args: list[str]) -> int:
    from rich.table import Table

    rows = ctx.host.assist.dispatch(["assist", "scenarios"])
    if not rows:
        ctx.console.print("[yellow]No assist scenarios registered.[/]")
        return 0

    table = Table(title="Assist Scenarios", show_lines=True)
    table.add_column("Scenario", style="green")
    table.add_column("Flow ID", style="cyan")
    table.add_column("Summary", style="dim")
    for row in rows:
        table.add_row(
            str(row.get("scenario_id", "")),
            str(row.get("flow_id", "")),
            str(row.get("summary", "")),
        )
    ctx.console.print(table)
    ctx.console.print(
        "[dim]Start a scenario:[/] [cyan]assist start <scenario_id>[/] "
        "[dim](e.g.[/] [cyan]assist start operator-entry[/][dim])[/]"
    )
    return 0


def cmd_assist_start(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] assist start <scenario_id>")
        return 1
    scenario_id = args[0]
    try:
        view = ctx.host.assist.start_scenario(scenario_id, {})
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    ctx.set_active_assist(view)
    render_assistant_panel(ctx.console, view)
    return 0


def cmd_assist_input(ctx: CliContext, args: list[str]) -> int:
    if not args:
        ctx.console.print("[red]Usage:[/] assist input <value>")
        return 1
    session_id = ctx.active_assist_session_id
    if not session_id:
        ctx.console.print("[red]No active assist session.[/] Run [cyan]assist start <scenario>[/].")
        return 1
    value = " ".join(args)
    try:
        handle = ctx.host.assist.session(session_id)
        view = handle.input(value, view_format="assistant").to_dict(view_format="assistant")
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    ctx.set_active_assist(view)
    render_assistant_panel(ctx.console, view)
    return 0


def cmd_assist_handoff(ctx: CliContext, _args: list[str]) -> int:
    session_id = ctx.active_assist_session_id
    if not session_id:
        ctx.console.print("[red]No active assist session.[/]")
        return 1
    try:
        result = ctx.host.assist.handoff(session_id)
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1

    from rich.panel import Panel

    handoff = result.get("handoff") or {}
    kind = handoff.get("kind")
    if kind == "flow":
        flow_id = handoff.get("flow_id")
        body = (
            f"[bold green]Handoff ready[/] — start business flow [cyan]{flow_id}[/]\n\n"
            f"[dim]Next:[/] [cyan]flow start {flow_id}[/] or [cyan]start {flow_id}[/]"
        )
        ctx.console.print(Panel(body, title="Assist handoff", border_style="green"))
    else:
        hint = handoff.get("operator_hint") or "No business flow handoff for this session."
        ctx.console.print(Panel(hint, title="Assist handoff", border_style="yellow"))
    return 0


def cmd_assist_status(ctx: CliContext, args: list[str]) -> int:
    view_format = "assistant"
    session_id = ctx.active_assist_session_id
    positional: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--format" and index + 1 < len(args):
            view_format = args[index + 1]
            index += 2
            continue
        positional.append(token)
        index += 1

    if positional:
        session_id = positional[0]
    if not session_id:
        ctx.console.print("[red]No active assist session.[/] Run [cyan]assist start <scenario>[/].")
        return 1

    try:
        handle = ctx.host.assist.session(session_id)
        view = handle.context(view_format=view_format).to_dict(view_format=view_format)
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1

    if view_format == "assistant":
        render_assistant_panel(ctx.console, view)
    else:
        from rich.table import Table

        table = Table(title=f"Assist session {session_id[:12]}…", show_lines=True)
        table.add_column("Field", style="cyan")
        table.add_column("Value")
        for key in sorted(view):
            table.add_row(key, str(view[key]))
        ctx.console.print(table)
    return 0


def cmd_assist_cancel(ctx: CliContext, _args: list[str]) -> int:
    session_id = ctx.active_assist_session_id
    if not session_id:
        ctx.console.print("[red]No active assist session.[/]")
        return 1
    try:
        result = ctx.host.assist.session(session_id).cancel()
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    ctx.clear_active_assist()
    ctx.console.print(f"[yellow]Assist session cancelled.[/] {result}")
    return 0