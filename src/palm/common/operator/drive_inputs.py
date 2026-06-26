"""
Wizard drive macro — apply a sequence of operator inputs in one MCP call.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.input_coercion import resolve_mcp_wizard_input

_TERMINAL_STATUSES = frozenset({"SUCCESS", "FAILED", "CANCELLED"})


def drive_wizard_inputs(
    *,
    instance_id: str,
    inputs: Sequence[str],
    get_wizard: Callable[[str], dict[str, Any]],
    provide_input: Callable[[str, Any], dict[str, Any]],
    max_steps: int = 30,
) -> dict[str, Any]:
    """Apply ``inputs`` sequentially until wait, child-wait, terminal, or exhaustion."""
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1")

    pending = list(inputs)
    steps: list[dict[str, Any]] = []

    for _ in range(max_steps):
        view = get_wizard(instance_id)
        before = compact_wizard_inspect(view)
        status = str(before.get("status") or "")

        if status in _TERMINAL_STATUSES:
            return _drive_result(
                instance_id,
                stopped_reason="terminal",
                steps=steps,
                view=before,
                remaining=pending,
            )
        if before.get("waiting_for_child"):
            return _drive_result(
                instance_id,
                stopped_reason="waiting_for_child",
                steps=steps,
                view=before,
                remaining=pending,
            )
        if status != "WAITING_FOR_INPUT":
            return _drive_result(
                instance_id,
                stopped_reason="not_waiting_for_input",
                steps=steps,
                view=before,
                remaining=pending,
            )
        if not pending:
            return _drive_result(
                instance_id,
                stopped_reason="inputs_exhausted",
                steps=steps,
                view=before,
                remaining=pending,
            )

        raw_input = pending.pop(0)
        resolved = resolve_mcp_wizard_input(
            input=raw_input,
            value=None,
            wizard_view=view,
        )
        view = provide_input(instance_id, resolved)
        after = compact_wizard_inspect(view)
        steps.append(
            {
                "input": raw_input,
                "resolved": resolved,
                "step_before": before.get("step"),
                "step_after": after.get("step"),
                "status": after.get("status"),
            }
        )

    view = get_wizard(instance_id)
    return _drive_result(
        instance_id,
        stopped_reason="max_steps",
        steps=steps,
        view=compact_wizard_inspect(view),
        remaining=pending,
    )


def _drive_result(
    instance_id: str,
    *,
    stopped_reason: str,
    steps: list[dict[str, Any]],
    view: dict[str, Any],
    remaining: list[str],
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "instance_id": instance_id,
        "stopped_reason": stopped_reason,
        "steps_applied": len(steps),
        "steps": steps,
        "remaining_inputs": remaining,
        **view,
    }
    return payload


__all__ = ["drive_wizard_inputs"]