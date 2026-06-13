"""
CLI instance resolution — consistent refs across list, status, and snapshots.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.exceptions import InstanceNotFoundError
from palm.common.managers import InstanceSummary

if TYPE_CHECKING:
    from palm.runtimes.cli.pkg.context import CliContext


def resolve_instance_id(ctx: CliContext, ref: str) -> str:
    """
    Resolve an instance reference to a canonical ``instance_id``.

    Supports exact ids, unique prefixes (e.g. truncated table ids), and
    flow/process display names.
    """
    ref = ref.strip()
    if not ref:
        raise InstanceNotFoundError(ref)

    summaries = ctx.list_instance_summaries()
    known_ids = [summary.instance_id for summary in summaries]

    if ref in known_ids:
        return ref

    prefix_matches = [iid for iid in known_ids if iid.startswith(ref)]
    if len(prefix_matches) == 1:
        return prefix_matches[0]
    if len(prefix_matches) > 1:
        raise InstanceNotFoundError(
            f"Ambiguous instance prefix {ref!r} — matches: {', '.join(prefix_matches)}"
        )

    for summary in summaries:
        if _summary_matches_name(summary, ref):
            return summary.instance_id

    try:
        return ctx.instance_manager.get(ref).instance_id
    except InstanceNotFoundError as exc:
        raise InstanceNotFoundError(ref) from exc


def _summary_matches_name(summary: InstanceSummary, ref: str) -> bool:
    return summary.flow_name == ref or summary.process_name == ref
