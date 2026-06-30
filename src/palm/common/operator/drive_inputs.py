"""
Wizard drive macro — apply a sequence of operator inputs in one MCP call.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any

from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.input_coercion import resolve_mcp_wizard_input

_TERMINAL_STATUSES = frozenset({"SUCCESS", "SUCCEEDED", "FAILED", "CANCELLED"})


def drive_wizard_inputs(
    *,
    instance_id: str,
    inputs: Sequence[str],
    get_wizard: Callable[[str], dict[str, Any]],
    provide_input: Callable[[str, Any], dict[str, Any]],
    max_steps: int = 30,
    payload: Any = None,
    include_steps: bool = False,
    include_operator_hint: bool = False,
) -> dict[str, Any]:
    """Apply ``inputs`` sequentially until wait, child-wait, terminal, or exhaustion."""
    if max_steps < 1:
        raise ValueError("max_steps must be at least 1")

    pending = list(inputs)
    structured = payload
    steps: list[dict[str, Any]] = []
    compact_kwargs = {"include_operator_hint": include_operator_hint}

    for _ in range(max_steps):
        view = get_wizard(instance_id)
        before = compact_wizard_inspect(view, **compact_kwargs)
        status = str(before.get("status") or "")

        if status in _TERMINAL_STATUSES:
            return _drive_result(
                instance_id,
                stopped_reason="terminal",
                steps=steps,
                view=before,
                remaining=pending,
                include_steps=include_steps,
            )
        if before.get("waiting_for_child"):
            return _drive_result(
                instance_id,
                stopped_reason="waiting_for_child",
                steps=steps,
                view=before,
                remaining=pending,
                include_steps=include_steps,
            )
        if status != "WAITING_FOR_INPUT":
            return _drive_result(
                instance_id,
                stopped_reason="not_waiting_for_input",
                steps=steps,
                view=before,
                remaining=pending,
                include_steps=include_steps,
            )
        if not pending and structured is None:
            return _drive_result(
                instance_id,
                stopped_reason="inputs_exhausted",
                steps=steps,
                view=before,
                remaining=pending,
                include_steps=include_steps,
            )

        if structured is not None:
            resolved = structured
            raw_input = "<payload>"
            structured = None
        else:
            raw_input = pending.pop(0)
            resolved = resolve_mcp_wizard_input(
                input=raw_input,
                value=None,
                wizard_view=view,
            )
        view = provide_input(instance_id, resolved)
        after = compact_wizard_inspect(view, **compact_kwargs)
        steps.append(
            {
                "input": raw_input,
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
        view=compact_wizard_inspect(view, **compact_kwargs),
        remaining=pending,
        include_steps=include_steps,
    )


def _drive_result(
    instance_id: str,
    *,
    stopped_reason: str,
    steps: list[dict[str, Any]],
    view: dict[str, Any],
    remaining: list[str],
    include_steps: bool = False,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "instance_id": instance_id,
        "stopped_reason": stopped_reason,
        "steps_applied": len(steps),
        "remaining_inputs": remaining,
        **view,
    }
    if include_steps:
        payload["steps"] = steps
    return payload


__all__ = ["drive_wizard_inputs"]
