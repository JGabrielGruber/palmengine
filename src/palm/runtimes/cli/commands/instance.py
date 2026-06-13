"""Instance commands — list, snapshots, prune."""

from __future__ import annotations

from palm.runtimes.cli.commands.views import render_instance_table
from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.shared.instance_ops import (
    filter_summaries,
    parse_instance_list_flags,
    prune_terminal_instances,
)
from palm.runtimes.cli.shared.output import emit_json, snapshots_to_json, summaries_payload


def cmd_instance_list(ctx: CliContext, args: list[str]) -> int:
    options, _remaining = parse_instance_list_flags(args)
    if "--format" in args:
        index = args.index("--format")
        if index + 1 < len(args) and args[index + 1] == "json":
            ctx.output_format = "json"

    summaries = filter_summaries(
        ctx.list_instance_summaries(),
        options=options,
    )
    if ctx.output_format == "json":
        emit_json(ctx.console, summaries_payload(summaries))
        return 0

    hint = None
    if not options.include_all:
        hint = (
            "Showing active (non-terminal) instances — append [cyan]--all[/] to include completed."
        )
    render_instance_table(ctx.console, summaries, hint=hint)
    return 0


def cmd_instance_snapshots(ctx: CliContext, args: list[str]) -> int:
    from rich.table import Table

    if not args:
        ctx.console.print("[red]Usage:[/] instance snapshots <instance_id>")
        return 1
    try:
        instance_id = ctx.resolve_instance_id(args[0])
        snapshots = ctx.list_instance_snapshots(instance_id)
    except Exception as exc:
        ctx.console.print(f"[red]{exc}[/]")
        return 1
    if ctx.output_format == "json":
        emit_json(
            ctx.console,
            {"instance_id": instance_id, "snapshots": snapshots_to_json(snapshots)},
        )
        return 0

    if not snapshots:
        ctx.console.print("[yellow]No state snapshots recorded for this instance.[/]")
        ctx.console.print(
            "[dim]Enable with[/] [cyan]PALM_ENABLE_STATE_SNAPSHOT=true[/] "
            "[dim]or[/] [cyan]--enable-state-snapshot[/]"
        )
        return 0

    table = Table(title=f"State Snapshots — {instance_id[:20]}", show_lines=True)
    table.add_column("#", justify="right", style="dim")
    table.add_column("Status", style="yellow")
    table.add_column("Recorded At", style="cyan")
    table.add_column("Step")
    table.add_column("Job", style="dim")
    for index, snapshot in enumerate(snapshots, start=1):
        table.add_row(
            str(index),
            snapshot.status,
            snapshot.recorded_at,
            snapshot.wizard_step_slug or "—",
            snapshot.job_id[:14],
        )
    ctx.console.print(table)
    return 0


def cmd_instance_prune(ctx: CliContext, args: list[str]) -> int:
    dry_run = "--dry-run" in args
    removed = prune_terminal_instances(ctx, dry_run=dry_run)
    if ctx.output_format == "json":
        emit_json(ctx.console, {"dry_run": dry_run, "removed": removed})
        return 0
    label = "Would remove" if dry_run else "Removed"
    if not removed:
        ctx.console.print("[dim]No terminal instances to prune.[/]")
        return 0
    ctx.console.print(f"[green]{label}[/] {len(removed)} instance(s):")
    for instance_id in removed:
        ctx.console.print(f"  • {instance_id}")
    return 0