"""
Instance listing, filtering, and maintenance helpers for the CLI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from palm.common.managers import InstanceSummary
from palm.core.orchestration import JobStatus
from palm.runtimes.cli.shared.context import CliContext

_TERMINAL = frozenset(
    {
        JobStatus.SUCCEEDED.value,
        JobStatus.FAILED.value,
        JobStatus.CANCELLED.value,
    }
)

_STATUS_EMOJI = {
    JobStatus.PENDING.value: "⏳",
    JobStatus.RUNNING.value: "▶",
    JobStatus.WAITING_FOR_INPUT.value: "⌨",
    JobStatus.SUCCEEDED.value: "✓",
    JobStatus.FAILED.value: "✗",
    JobStatus.CANCELLED.value: "⊘",
}


@dataclass
class InstanceListOptions:
    status: str | None = None
    flow: str | None = None
    limit: int | None = None
    include_all: bool = False


def status_emoji(status: str) -> str:
    return _STATUS_EMOJI.get(status, "•")


def is_terminal_status(status: str) -> bool:
    return status in _TERMINAL


def short_instance_id(instance_id: str, *, length: int = 12) -> str:
    return instance_id if len(instance_id) <= length else f"{instance_id[:length]}…"


def filter_summaries(
    summaries: list[InstanceSummary],
    *,
    options: InstanceListOptions,
) -> list[InstanceSummary]:
    filtered = list(summaries)
    if not options.include_all:
        filtered = [item for item in filtered if not is_terminal_status(item.status)]
    if options.status:
        needle = options.status.upper()
        filtered = [item for item in filtered if item.status.upper() == needle]
    if options.flow:
        needle = options.flow.lower()
        filtered = [
            item
            for item in filtered
            if (item.flow_name or "").lower() == needle or needle in (item.flow_name or "").lower()
        ]
    if options.limit is not None and options.limit > 0:
        filtered = filtered[: options.limit]
    return filtered


def parse_instance_list_flags(args: list[str]) -> tuple[InstanceListOptions, list[str]]:
    options = InstanceListOptions()
    remaining: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--all":
            options.include_all = True
        elif token == "--status" and index + 1 < len(args):
            index += 1
            options.status = args[index]
        elif token == "--flow" and index + 1 < len(args):
            index += 1
            options.flow = args[index]
        elif token == "--limit" and index + 1 < len(args):
            index += 1
            options.limit = int(args[index])
        elif token.startswith("--"):
            remaining.append(token)
        else:
            remaining.append(token)
        index += 1
    return options, remaining


def prune_terminal_instances(ctx: CliContext, *, dry_run: bool = False) -> list[str]:
    """Delete persisted instances in terminal statuses."""
    removed: list[str] = []
    for summary in ctx.list_instance_summaries():
        if not is_terminal_status(summary.status):
            continue
        if dry_run:
            removed.append(summary.instance_id)
            continue
        if ctx.instance_manager.delete(summary.instance_id):
            removed.append(summary.instance_id)
    return removed


def summary_to_dict(summary: InstanceSummary) -> dict[str, Any]:
    from palm.runtimes.cli.shared.job_inspect import format_step_context

    return {
        "instance_id": summary.instance_id,
        "short_id": short_instance_id(summary.instance_id),
        "job_id": summary.job_id,
        "status": summary.status,
        "flow_name": summary.flow_name,
        "process_name": summary.process_name,
        "wizard_step_slug": summary.wizard_step_slug,
        "context": format_step_context(summary.wizard_step_slug),
        "updated_at": summary.updated_at,
        "snapshot_count": summary.snapshot_count,
    }
