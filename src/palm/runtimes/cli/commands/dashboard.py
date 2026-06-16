"""
Status dashboard — projection-backed host overview for the CLI.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Any

from palm import __version__
from palm.runtimes.cli.shared.instance_ops import is_terminal_status, short_instance_id, status_emoji
from palm.runtimes.cli.shared.runtime_display import runtime_names_plain

if TYPE_CHECKING:
    from palm.runtimes.cli.shared.context import CliContext


def render_status_dashboard(ctx: CliContext) -> int:
    """Render a Rich dashboard from host projections and coordination state."""
    from rich.columns import Columns
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    host = ctx.host
    console = ctx.console

    instances = host.list_instance_views(include_terminal=True)
    active_instances = [row for row in instances if not is_terminal_status(row.status)]
    jobs = host.list_job_views(limit=8)
    wizards = host.list_wizard_progress_views(limit=8, active_only=True)

    status_counts = Counter(row.status for row in instances)
    total = len(instances)
    active_count = len(active_instances)

    # Header
    header = Panel(
        f"[bold]Palm Engine[/] [dim]v{__version__}[/]\n"
        f"🌴 [bold]Status Dashboard[/] — live projection read models",
        border_style="cyan",
        padding=(0, 1),
    )

    # Host health
    health = Table(show_header=False, box=None, padding=(0, 1))
    health.add_column(style="dim", width=18)
    health.add_column()
    health.add_row("Roles", ", ".join(sorted(host.profile.roles)) or "—")
    health.add_row("Runtimes", runtime_names_plain(host))
    health.add_row("Storage", host.storage.backend_name or "(none)")
    if host.outbox_service is not None:
        pending = host.outbox_service.store.pending_count()
        health.add_row("Outbox", f"{pending} pending")
    else:
        health.add_row("Outbox", "[dim]not running[/]")
    recovery = host.last_recovery
    if recovery:
        workers = recovery.get("workers") or []
        health.add_row("Workers", ", ".join(workers) if workers else "—")
        outbox_pending = recovery.get("outbox_pending")
        if outbox_pending is not None:
            health.add_row("Recovery outbox", str(outbox_pending))
        projections = recovery.get("projections")
        if isinstance(projections, dict):
            counts = projections.get("counts")
            if isinstance(counts, dict):
                health.add_row(
                    "Projections",
                    ", ".join(f"{name}={count}" for name, count in sorted(counts.items())),
                )
    host_panel = Panel(health, title="🏠 Host", border_style="green")

    # Instance summary
    inst_table = Table(title="📊 Instances", show_lines=False, expand=True)
    inst_table.add_column("Status", style="bold")
    inst_table.add_column("Count", justify="right")
    inst_table.add_column("", style="dim")
    if status_counts:
        for status, count in sorted(status_counts.items(), key=lambda item: (-item[1], item[0])):
            inst_table.add_row(
                f"{status_emoji(status)} {status}",
                str(count),
                _bar(count, total),
            )
    else:
        inst_table.add_row("[dim]—[/]", "0", "")
    inst_table.caption = f"{active_count} active · {total} total"
    inst_panel = Panel(inst_table, border_style="blue")

    # Active wizards
    wiz_table = Table(title="🧙 Active Wizards", show_lines=False, expand=True)
    wiz_table.add_column("Instance", style="cyan", no_wrap=True)
    wiz_table.add_column("Wizard")
    wiz_table.add_column("Step")
    wiz_table.add_column("Backtracks", justify="right")
    wiz_table.add_column("Commit")
    if wizards:
        for entry in wizards:
            iid = short_instance_id(entry.instance_id or entry.key, length=10)
            trace_len = len(entry.backtrack_trace)
            commit = entry.commit_status or "—"
            if entry.commit_error:
                commit = f"[red]{commit}[/]"
            wiz_table.add_row(
                iid,
                entry.wizard_name or "—",
                entry.current_step or "—",
                str(trace_len) if trace_len else "—",
                commit,
            )
            if entry.backtrack_trace:
                last = entry.backtrack_trace[-1]
                detail = f"  [dim]↩ {last.from_step or '?'} → {last.to_step or '?'}[/]"
                wiz_table.add_row("", "", detail, "", "")
    else:
        wiz_table.add_row("[dim]No active wizard sessions[/]", "", "", "", "")
    wiz_panel = Panel(wiz_table, border_style="magenta")

    # Job board
    job_table = Table(title="⚡ Recent Jobs", show_lines=False, expand=True)
    job_table.add_column("Job", style="cyan", no_wrap=True)
    job_table.add_column("Status")
    job_table.add_column("Instance", style="dim")
    job_table.add_column("Updated", style="dim", no_wrap=True)
    if jobs:
        for row in jobs:
            job_table.add_row(
                short_instance_id(row.job_id, length=10),
                f"{status_emoji(row.status)} {row.status}",
                short_instance_id(row.instance_id, length=10) if row.instance_id else "—",
                _short_time(row.updated_at),
            )
    else:
        job_table.add_row("[dim]No jobs tracked yet[/]", "", "", "")
    job_panel = Panel(job_table, border_style="yellow")

    # Recent host events
    events_table = Table(title="📡 Recent Host Events", show_lines=False, expand=True)
    events_table.add_column("Time", style="dim", no_wrap=True)
    events_table.add_column("Event", style="cyan")
    events_table.add_column("Detail", style="dim")
    recent = host.recent_host_events(limit=8)
    if recent:
        for recorded in reversed(recent):
            events_table.add_row(
                _short_time(recorded.timestamp),
                recorded.type,
                _event_detail(recorded.payload),
            )
    else:
        events_table.add_row("—", "[dim]No events recorded yet[/]", "")
    events_panel = Panel(events_table, border_style="dim")

    footer = Text(
        "Tip: status <id> for instance detail · doctor for full health · doctor --dashboard for this view",
        style="dim",
    )

    console.print(
        Group(
            header,
            Columns([host_panel, inst_panel], equal=True, expand=True),
            wiz_panel,
            Columns([job_panel, events_panel], equal=True, expand=True),
            footer,
        )
    )
    return 0


def _bar(count: int, total: int, *, width: int = 12) -> str:
    if total <= 0:
        return ""
    filled = max(1, round(width * count / total)) if count else 0
    return "█" * filled + "░" * (width - filled)


def _short_time(iso_timestamp: str) -> str:
    if not iso_timestamp:
        return "—"
    if "T" in iso_timestamp:
        return iso_timestamp.split("T", 1)[1][:8]
    return iso_timestamp[:19]


def _event_detail(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    parts: list[str] = []
    for key in ("command", "count", "name", "roles", "primary", "error"):
        if key in payload and payload[key] is not None:
            value = payload[key]
            if isinstance(value, list):
                value = ",".join(str(item) for item in value)
            parts.append(f"{key}={value}")
    return " ".join(parts[:3])