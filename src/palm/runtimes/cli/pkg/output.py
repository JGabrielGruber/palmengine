"""CLI output helpers — JSON scripting and shared serializers."""

from __future__ import annotations

import json
from typing import Any

from palm.instances import StateSnapshot
from palm.runtimes.cli.pkg.instance_ops import summary_to_dict


def emit_json(console: Any, payload: Any) -> None:
    if hasattr(console, "print_json"):
        console.print_json(data=payload)
        return
    console.print(json.dumps(payload, indent=2, default=str))


def snapshots_to_json(snapshots: list[StateSnapshot]) -> list[dict[str, Any]]:
    return [
        {
            "status": snap.status,
            "recorded_at": snap.recorded_at,
            "wizard_step_slug": snap.wizard_step_slug,
            "job_id": snap.job_id,
            "state_snapshot": snap.state_snapshot,
        }
        for snap in snapshots
    ]


def summaries_payload(summaries: list[Any]) -> list[dict[str, Any]]:
    return [summary_to_dict(item) for item in summaries]
