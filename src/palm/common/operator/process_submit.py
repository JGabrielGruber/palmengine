"""
Process submit validation — prevent catalog processes from spawning all flows.
"""

from __future__ import annotations

from typing import Any


def process_submit_hints(process: dict[str, Any]) -> list[str]:
    """Build suggested wizard entry hints from process metadata."""
    metadata = process.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    hints: list[str] = []
    mcp = metadata.get("mcp")
    if isinstance(mcp, dict):
        entries = mcp.get("entries")
        if isinstance(entries, dict):
            for name, entry in entries.items():
                if not isinstance(entry, dict):
                    continue
                submit = entry.get("submit")
                if isinstance(submit, str) and submit:
                    hints.append(f"{name}: {submit}")
                    continue
                flow = entry.get("flow")
                if isinstance(flow, str) and flow:
                    hints.append(
                        f'{name}: palm_submit_wizard(flow_name="{flow}")'
                    )

    entry_flow = metadata.get("entry_flow")
    if isinstance(entry_flow, str) and entry_flow:
        hint = f'palm_submit_wizard(flow_name="{entry_flow}")'
        if hint not in hints:
            hints.append(hint)

    return hints


def is_interactive_process_catalog(process: dict[str, Any]) -> bool:
    """True when the process declares wizard/menu entry metadata."""
    metadata = process.get("metadata")
    if not isinstance(metadata, dict):
        return False
    if metadata.get("entry_flow"):
        return True
    mcp = metadata.get("mcp")
    return isinstance(mcp, dict) and bool(mcp.get("entries"))


def validate_process_submit(process: dict[str, Any], *, mode: str = "default") -> None:
    """Reject submit_process on interactive catalogs unless mode is all_flows."""
    if mode == "all_flows":
        return
    if not is_interactive_process_catalog(process):
        return

    name = process.get("name") or process.get("process_id") or "process"
    flows = process.get("flows")
    flow_count = len(flows) if isinstance(flows, list) else 0
    hints = process_submit_hints(process)
    hint_text = "; ".join(hints) if hints else "palm_submit_wizard(flow_name=entry_flow)"
    raise ValueError(
        f"Process {name!r} is an interactive catalog ({flow_count} flows), "
        "not a single entry point. Use palm_submit_wizard instead of "
        f"palm_submit_process. Suggested: {hint_text}. "
        "Pass mode='all_flows' only for true multi-flow pipelines."
    )


__all__ = [
    "is_interactive_process_catalog",
    "process_submit_hints",
    "validate_process_submit",
]