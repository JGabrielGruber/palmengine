"""Flow session view shaping — shared by REST and MCP operator surfaces."""

from __future__ import annotations

from typing import Any

from palm.common.operator.compact import compact_wizard_inspect
from palm.common.operator.session_view_registry import iter_session_view_enrichers
from palm.common.operator.view_registry import (
    OperatorViewContext,
    build_operator_view,
    normalize_view_format,
)


def shape_flow_session_view(
    flat: dict[str, Any],
    *,
    format: str = "powertool",
    session_id: str | None = None,
    flow_id: str | None = None,
    path: list[str] | None = None,
    invoke_tree: dict[str, Any] | None = None,
    include: list[str] | None = None,
    truncate_answers_at: int = 2000,
    stored_mutation_gate: dict[str, Any] | None = None,
    include_input_schema: bool = False,
    scenario_id: str | None = None,
    handoff_ready: bool = False,
    intent: str | None = None,
    answers_preview: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Shape a flattened flow session inspect view for operator consumers."""
    fmt = normalize_view_format(format or "powertool")
    if fmt == "verbose":
        return dict(flat)
    if fmt == "assistant":
        sid = session_id or flat.get("instance_id") or flat.get("session_id")
        fid = flow_id or flat.get("flow_name") or flat.get("flow")
        # 0.32.5 — infer assist scenario / handoff when driving via flows path
        scen = scenario_id or _scenario_id_from_flat(flat)
        hready = handoff_ready or _handoff_ready_from_flat(flat)
        intent_val = intent or _intent_from_flat(flat)
        preview = answers_preview
        if preview is None and intent_val is not None:
            preview = {"intent": intent_val}
        context = OperatorViewContext(
            session_id=str(sid) if sid is not None else None,
            flow_id=str(fid) if fid is not None else None,
            scenario_id=str(scen) if scen is not None else None,
            invoke_tree=invoke_tree,
            path=list(path or []),
            stored_mutation_gate=stored_mutation_gate,
            include_input_schema=include_input_schema,
            handoff_ready=hready,
            intent=str(intent_val) if intent_val is not None else None,
            answers_preview=preview,
        )
        payload = build_operator_view("assistant", flat_view=flat, context=context)
        # Attach assist session verbs when this flow is an assist scenario.
        # Domains register enrichers downward (see session_view_registry); common
        # never imports assist. Each enricher is best-effort — failures are skipped.
        if scen and sid:
            status_val = str(flat.get("status") or payload.get("status") or "")
            for enrich in iter_session_view_enrichers():
                try:
                    payload = enrich(
                        payload,
                        session_id=str(sid),
                        scenario_id=str(scen),
                        handoff_ready=hready,
                        status=status_val,
                    )
                except Exception:
                    continue
        return payload
    return compact_wizard_inspect(
        flat,
        format="compact",
        include=include,
        truncate_answers_at=truncate_answers_at,
        stored_mutation_gate=stored_mutation_gate,
    )


def _scenario_id_from_flat(flat: dict[str, Any]) -> str | None:
    pattern = flat.get("pattern")
    if isinstance(pattern, dict):
        meta = pattern.get("metadata") or {}
        if isinstance(meta, dict):
            assist = meta.get("assist") or {}
            if isinstance(assist, dict) and assist.get("scenario_id"):
                return str(assist["scenario_id"])
    meta = flat.get("metadata")
    if isinstance(meta, dict):
        assist = meta.get("assist") or {}
        if isinstance(assist, dict) and assist.get("scenario_id"):
            return str(assist["scenario_id"])
    if flat.get("scenario_id"):
        return str(flat["scenario_id"])
    return None


def _handoff_ready_from_flat(flat: dict[str, Any]) -> bool:
    """True only for assist-scenario handoff moments — not every finished flow.

    Business flows (todo-builder, …) complete without handoff; treating all
    SUCCEEDED/summary turns as handoff-ready poisoned Portal finish chrome (0.32.9).
    """
    scenario_id = _scenario_id_from_flat(flat)
    intent = _intent_from_flat(flat)
    if not scenario_id and not intent:
        return False
    status = str(flat.get("status") or "")
    if status in {"SUCCEEDED", "complete", "SUCCESS"}:
        return True
    step_kind = flat.get("step_kind")
    if step_kind == "summary":
        return True
    prompt = flat.get("prompt")
    if isinstance(prompt, dict) and prompt.get("step_kind") == "summary":
        return True
    return False


def _intent_from_flat(flat: dict[str, Any]) -> str | None:
    for key in ("answers", "answers_preview"):
        block = flat.get(key)
        if isinstance(block, dict) and block.get("intent") is not None:
            return str(block["intent"])
    pattern = flat.get("pattern")
    if isinstance(pattern, dict):
        answers = pattern.get("answers")
        if isinstance(answers, dict) and answers.get("intent") is not None:
            return str(answers["intent"])
    return None


__all__ = ["shape_flow_session_view"]