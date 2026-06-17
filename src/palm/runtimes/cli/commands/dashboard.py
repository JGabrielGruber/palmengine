"""
Status dashboard — projection-backed host overview for the CLI.

Reads exclusively from ApplicationHost CQRS queries and the host event recorder.
"""

from __future__ import annotations

import time
from collections import Counter
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from palm import __version__
from palm.runtimes.cli.shared.instance_ops import (
    is_terminal_status,
    short_instance_id,
    status_emoji,
)
from palm.runtimes.cli.shared.runtime_display import runtime_names_plain

if TYPE_CHECKING:
    from palm.app.host.event_recorder import RecordedEvent
    from palm.common.cqrs.projections.instance_index import InstanceReadModel
    from palm.common.cqrs.projections.job_status_board import JobStatusReadModel
    from palm.common.cqrs.projections.wizard_progress import WizardProgressReadModel
    from palm.runtimes.cli.shared.context import CliContext

DEFAULT_REFRESH_INTERVAL = 2.0


@dataclass(frozen=True)
class DashboardOptions:
    """Render options for the status dashboard."""

    full: bool = False
    refresh_interval: float | None = None


@dataclass(frozen=True)
class DashboardSnapshot:
    """Single-pass projection read snapshot for fast render + refresh."""

    collected_at: datetime
    instances: tuple[InstanceReadModel, ...]
    jobs: tuple[JobStatusReadModel, ...]
    wizards: tuple[WizardProgressReadModel, ...]
    events: tuple[RecordedEvent, ...]
    recovery: dict[str, Any] | None


def parse_dashboard_args(args: list[str]) -> tuple[DashboardOptions, list[str]]:
    """Parse dashboard flags; return options and any unconsumed args."""
    full = False
    refresh: float | None = None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--full":
            full = True
            index += 1
            continue
        if arg in ("--refresh", "-r"):
            index += 1
            if index < len(args) and _looks_numeric(args[index]):
                refresh = float(args[index])
                index += 1
            else:
                refresh = DEFAULT_REFRESH_INTERVAL
            continue
        if arg == "--dashboard":
            index += 1
            continue
        break
    return DashboardOptions(full=full, refresh_interval=refresh), args[index:]


def run_status_dashboard(ctx: CliContext, options: DashboardOptions | None = None) -> int:
    """Render dashboard once or enter a refresh loop when requested."""
    opts = options or DashboardOptions()
    if opts.refresh_interval is not None and not _is_interactive(ctx):
        opts = replace(opts, refresh_interval=None)
    if opts.refresh_interval is not None:
        return _refresh_loop(ctx, opts)
    return render_status_dashboard(ctx, opts)


def render_status_dashboard(ctx: CliContext, options: DashboardOptions | None = None) -> int:
    """Render a Rich dashboard from a cached projection snapshot."""
    from rich.columns import Columns
    from rich.console import Group
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text

    opts = options or DashboardOptions()
    snapshot = _collect_snapshot(ctx, opts)
    host = ctx.host
    console = ctx.console

    instances = list(snapshot.instances)
    active_instances = [row for row in instances if not is_terminal_status(row.status)]
    jobs = list(snapshot.jobs)
    wizards = list(snapshot.wizards)
    status_counts = Counter(row.status for row in instances)
    total = len(instances)
    active_count = len(active_instances)

    job_limit = 12 if opts.full else 8
    event_limit = 12 if opts.full else 6
    wizard_limit = 10 if opts.full else 6

    # Header + KPI strip
    mode = "full detail" if opts.full else "live"
    refreshed = _format_clock(snapshot.collected_at)
    header = Panel(
        Text.from_markup(
            f"[bold]Palm Engine[/] [dim]v{__version__}[/]  "
            f"🌴 [bold cyan]Status Dashboard[/] [dim]({mode})[/]\n"
            f"[dim]Projection read models · updated {refreshed}[/]"
        ),
        border_style="cyan",
        padding=(0, 1),
    )

    kpi = Table.grid(expand=True)
    kpi.add_column(justify="center")
    kpi.add_column(justify="center")
    kpi.add_column(justify="center")
    kpi.add_column(justify="center")
    outbox_pending = _outbox_pending(host)
    kpi.add_row(
        _kpi_cell("Active", str(active_count), "blue"),
        _kpi_cell("Wizards", str(len(wizards)), "magenta"),
        _kpi_cell("Outbox", str(outbox_pending), "yellow" if outbox_pending else "green"),
        _kpi_cell("Jobs", str(len(jobs)), "cyan"),
    )
    kpi_panel = Panel(kpi, title="At a glance", border_style="bright_blue", padding=(0, 1))

    # Host health
    health = Table(show_header=False, box=None, padding=(0, 1))
    health.add_column(style="dim", width=16)
    health.add_column()
    health.add_row("Roles", ", ".join(sorted(host.profile.roles)) or "—")
    health.add_row("Runtimes", runtime_names_plain(host))
    health.add_row("Storage", host.storage.backend_name or "(none)")
    health.add_row("Outbox", _outbox_label(host))
    recovery = snapshot.recovery
    if recovery:
        workers = recovery.get("workers") or []
        ready = recovery.get("workers_ready")
        ready_style = "green" if ready else "yellow"
        health.add_row("Workers", f"[{ready_style}]{', '.join(workers) if workers else '—'}[/]")
        if recovery.get("outbox_pending") is not None:
            health.add_row("Recovery outbox", str(recovery["outbox_pending"]))
        projections = recovery.get("projections")
        if isinstance(projections, dict):
            counts = projections.get("counts")
            if isinstance(counts, dict):
                health.add_row(
                    "Projections",
                    ", ".join(f"{name}={count}" for name, count in sorted(counts.items())),
                )
        if opts.full:
            health.add_row("Primary", str(recovery.get("primary") or host.app.primary_name or "—"))
    host_panel = Panel(health, title="🏠 Host", border_style="green")

    # Instance breakdown
    inst_table = Table(title="📊 Instances by status", show_lines=False, expand=True)
    inst_table.add_column("Status", style="bold")
    inst_table.add_column("Count", justify="right")
    inst_table.add_column("Share", justify="right", style="dim")
    inst_table.add_column("", style="dim")
    if status_counts:
        for status, count in sorted(status_counts.items(), key=lambda item: (-item[1], item[0])):
            share = f"{100 * count / total:.0f}%" if total else "—"
            inst_table.add_row(
                f"{status_emoji(status)} {status}",
                str(count),
                share,
                _bar(count, total),
            )
    else:
        inst_table.add_row("[dim]—[/]", "0", "—", "")
    inst_table.caption = f"{active_count} active · {total} total"
    inst_panel = Panel(inst_table, border_style="blue")

    # Active instance rows (full mode)
    active_panel = None
    if opts.full and active_instances:
        active_sorted = sorted(active_instances, key=lambda row: row.updated_at, reverse=True)[:10]
        active_table = Table(title="🟢 Active instances", show_lines=False, expand=True)
        active_table.add_column("ID", style="cyan", no_wrap=True)
        active_table.add_column("Flow")
        active_table.add_column("Status")
        active_table.add_column("Step", style="dim")
        active_table.add_column("Updated", style="dim", no_wrap=True)
        for inst in active_sorted:
            flow = inst.flow_name or inst.process_name or "—"
            step = inst.wizard_step_slug or "—"
            active_table.add_row(
                short_instance_id(inst.instance_id, length=12),
                flow,
                f"{status_emoji(inst.status)} {inst.status}",
                step,
                _ago(inst.updated_at, snapshot.collected_at),
            )
        active_panel = Panel(active_table, border_style="bright_green")

    # Wizards
    wiz_table = Table(title="🧙 Wizard sessions", show_lines=False, expand=True)
    wiz_table.add_column("Instance", style="cyan", no_wrap=True)
    wiz_table.add_column("Wizard")
    wiz_table.add_column("Progress")
    wiz_table.add_column("Step")
    wiz_table.add_column("↩", justify="right")
    wiz_table.add_column("Commit")
    if wizards:
        for entry in wizards[:wizard_limit]:
            iid = short_instance_id(entry.instance_id or entry.key, length=10)
            completed = len(entry.completed_steps)
            progress = f"{completed} done" if completed else "—"
            if opts.full and entry.completed_steps:
                tail = ", ".join(entry.completed_steps[-3:])
                progress = f"{completed} ({tail})"
            trace_len = len(entry.backtrack_trace)
            commit = entry.commit_status or "—"
            if entry.commit_error:
                commit = f"[red]{commit}[/]"
            wiz_table.add_row(
                iid,
                entry.wizard_name or "—",
                progress,
                entry.current_step or "—",
                str(trace_len) if trace_len else "—",
                commit,
            )
            if entry.backtrack_trace:
                trace = entry.backtrack_trace if opts.full else entry.backtrack_trace[-2:]
                for hop in trace:
                    arrow = f"↩ {hop.from_step or '?'} → {hop.to_step or '?'}"
                    if hop.blocked:
                        arrow += f" [red](blocked: {hop.reason or 'yes'})[/]"
                    wiz_table.add_row("", "", f"[dim]{arrow}[/]", "", "", "")
    else:
        wiz_table.add_row("[dim]No active wizard sessions[/]", "", "", "", "", "")
    wiz_panel = Panel(wiz_table, border_style="magenta")

    # Job board
    throughput = _job_throughput_hint(jobs, snapshot.collected_at)
    job_table = Table(
        title=f"⚡ Job board [dim]({throughput})[/]" if throughput else "⚡ Job board",
        show_lines=False,
        expand=True,
    )
    job_table.add_column("Job", style="cyan", no_wrap=True)
    job_table.add_column("Status")
    job_table.add_column("Instance", style="dim")
    job_table.add_column("Age", style="dim", no_wrap=True)
    if opts.full:
        job_table.add_column("Updated", style="dim", no_wrap=True)
    if jobs:
        for job_row in jobs[:job_limit]:
            cells = [
                short_instance_id(job_row.job_id, length=10),
                f"{status_emoji(job_row.status)} {job_row.status}",
                short_instance_id(job_row.instance_id, length=10) if job_row.instance_id else "—",
                _ago(job_row.updated_at, snapshot.collected_at),
            ]
            if opts.full:
                cells.append(_short_time(job_row.updated_at))
            job_table.add_row(*cells)
    else:
        empty = ["[dim]No jobs tracked yet[/]", "", "", ""]
        if opts.full:
            empty.append("")
        job_table.add_row(*empty)
    job_panel = Panel(job_table, border_style="yellow")

    # Events
    events_table = Table(title="📡 Host events", show_lines=False, expand=True)
    events_table.add_column("Age", style="dim", no_wrap=True)
    events_table.add_column("Event")
    events_table.add_column("Detail", style="dim")
    recent = list(snapshot.events)[-event_limit:]
    if recent:
        for recorded in reversed(recent):
            events_table.add_row(
                _ago(recorded.timestamp, snapshot.collected_at),
                _event_type_styled(recorded.type),
                _event_detail(recorded.payload),
            )
    else:
        events_table.add_row("—", "[dim]No events recorded yet[/]", "")
    events_panel = Panel(events_table, border_style="dim")

    refresh_hint = ""
    if opts.refresh_interval:
        refresh_hint = f" · refresh {opts.refresh_interval:.0f}s"
    elif _is_interactive(ctx):
        refresh_hint = " · [cyan]status -r[/] to live-refresh"
    footer = Text.from_markup(
        f"[dim]Tip: status <id> detail · status --full deeper view · doctor health"
        f"{refresh_hint}[/]"
    )

    body_top = Columns([host_panel, inst_panel], equal=True, expand=True)
    body_mid: list[Any] = [wiz_panel]
    if active_panel is not None:
        body_mid.insert(0, active_panel)
    body_bottom = Columns([job_panel, events_panel], equal=True, expand=True)

    console.print(Group(header, kpi_panel, body_top, *body_mid, body_bottom, footer))
    return 0


def _collect_snapshot(ctx: CliContext, options: DashboardOptions) -> DashboardSnapshot:
    host = ctx.host
    instance_limit = 50 if options.full else None
    return DashboardSnapshot(
        collected_at=datetime.now(UTC),
        instances=tuple(host.list_instance_views(include_terminal=True, limit=instance_limit)),
        jobs=tuple(host.list_job_views(limit=16)),
        wizards=tuple(host.list_wizard_progress_views(limit=12, active_only=True)),
        events=tuple(host.recent_host_events(limit=16)),
        recovery=host.last_recovery,
    )


def _refresh_loop(ctx: CliContext, options: DashboardOptions) -> int:
    interval = options.refresh_interval or DEFAULT_REFRESH_INTERVAL
    try:
        while True:
            if _is_interactive(ctx):
                ctx.console.clear()
            render_status_dashboard(ctx, options)
            ctx.console.print(f"[dim]Live refresh every {interval:.0f}s — Ctrl+C to stop[/]")
            time.sleep(interval)
    except KeyboardInterrupt:
        ctx.console.print("[dim]Dashboard stopped.[/]")
    return 0


def _is_interactive(ctx: CliContext) -> bool:
    return bool(getattr(ctx.console, "is_terminal", False))


def _looks_numeric(value: str) -> bool:
    try:
        float(value)
    except ValueError:
        return False
    return True


def _outbox_pending(host: Any) -> int:
    if host.outbox_service is None:
        return 0
    return int(host.outbox_service.store.pending_count())


def _outbox_label(host: Any) -> str:
    if host.outbox_service is None:
        return "[dim]not running[/]"
    pending = _outbox_pending(host)
    if pending:
        return f"[yellow]{pending} pending[/]"
    return "[green]0 pending[/]"


def _kpi_cell(label: str, value: str, color: str) -> str:
    return f"[dim]{label}[/]\n[bold {color}]{value}[/]"


def _bar(count: int, total: int, *, width: int = 10) -> str:
    if total <= 0:
        return ""
    filled = max(1, round(width * count / total)) if count else 0
    return "[cyan]" + "█" * filled + "[/][dim]" + "░" * (width - filled) + "[/]"


def _short_time(iso_timestamp: str) -> str:
    if not iso_timestamp:
        return "—"
    if "T" in iso_timestamp:
        return iso_timestamp.split("T", 1)[1][:8]
    return iso_timestamp[:19]


def _parse_timestamp(iso_timestamp: str) -> datetime | None:
    if not iso_timestamp:
        return None
    text = iso_timestamp.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _ago(iso_timestamp: str, now: datetime) -> str:
    parsed = _parse_timestamp(iso_timestamp)
    if parsed is None:
        return "—"
    delta = now - parsed.astimezone(UTC)
    seconds = int(delta.total_seconds())
    if seconds < 5:
        return "now"
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m"
    if seconds < 86400:
        return f"{seconds // 3600}h"
    return f"{seconds // 86400}d"


def _format_clock(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%H:%M:%S UTC")


def _job_throughput_hint(jobs: list[JobStatusReadModel], now: datetime) -> str:
    from palm.core.orchestration import JobStatus

    if not jobs:
        return ""
    terminal = {
        JobStatus.SUCCEEDED.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELLED.value,
    }
    completed = sum(1 for row in jobs if row.status in terminal)
    active = len(jobs) - completed
    recent_done = 0
    for row in jobs:
        if row.status != JobStatus.SUCCEEDED.value:
            continue
        parsed = _parse_timestamp(row.updated_at)
        if parsed and (now - parsed.astimezone(UTC)).total_seconds() <= 300:
            recent_done += 1
    parts = [f"{active} active"]
    if completed:
        parts.append(f"{completed} done")
    if recent_done:
        parts.append(f"{recent_done} succeeded/5m")
    return " · ".join(parts)


def _event_type_styled(event_type: str) -> str:
    if event_type in {"host.started", "host.recovered", "host.workers.ready"}:
        return f"[green]{event_type}[/]"
    if event_type in {"host.shutdown", "host.webhook.failed"}:
        return f"[red]{event_type}[/]"
    if event_type.startswith("host.command"):
        return f"[cyan]{event_type}[/]"
    if event_type.startswith("host.outbox"):
        return f"[yellow]{event_type}[/]"
    if event_type.startswith("host.webhook"):
        return f"[magenta]{event_type}[/]"
    return f"[dim]{event_type}[/]"


def _event_detail(payload: dict[str, Any]) -> str:
    if not payload:
        return ""
    parts: list[str] = []
    for key in ("command", "count", "name", "roles", "primary", "error", "registered"):
        if key in payload and payload[key] is not None:
            value = payload[key]
            if isinstance(value, list):
                value = ",".join(str(item) for item in value)
            parts.append(f"{key}={value}")
    return " ".join(parts[:4])
