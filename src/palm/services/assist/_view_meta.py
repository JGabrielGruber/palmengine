"""Extract flow/scenario/answers metadata from inspect views."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.query import GetFlowQuery
from palm.services.assist.registry import list_scenario_rows

if TYPE_CHECKING:
    from palm.services.assist.service import AssistService


def flow_id_from_view(view: dict[str, Any]) -> str | None:
    for key in ("flow_name", "flow_id"):
        value = view.get(key)
        if value is not None and str(value) not in {"", "flow"}:
            return str(value)
    progress = view.get("wizard_progress")
    if isinstance(progress, dict):
        wizard_name = progress.get("wizard_name")
        if wizard_name:
            return str(wizard_name)
    pattern = view.get("pattern")
    if isinstance(pattern, dict):
        flow = pattern.get("flow")
        if flow is not None and str(flow) not in {"", "flow"}:
            return str(flow)
    return None


def assist_metadata_from_view(view: dict[str, Any]) -> dict[str, Any]:
    pattern = view.get("pattern")
    if isinstance(pattern, dict):
        meta = pattern.get("metadata") or {}
        if isinstance(meta, dict):
            assist = meta.get("assist") or {}
            if isinstance(assist, dict):
                return assist
    return {}


def scenario_id_from_view(view: dict[str, Any], flow_id: str | None) -> str | None:
    assist_meta = assist_metadata_from_view(view)
    scenario_id = assist_meta.get("scenario_id")
    if scenario_id is not None:
        return str(scenario_id)
    if flow_id is not None:
        normalized = flow_id.removeprefix("flow-")
        for row in list_scenario_rows():
            registered = str(row.get("flow_id") or "")
            if registered in {flow_id, f"flow-{normalized}"} or registered.removeprefix(
                "flow-"
            ) == normalized:
                return str(row["scenario_id"])
    return None


def assist_metadata(service: AssistService, flow_id: str | None) -> dict[str, Any]:
    if flow_id is None:
        return {}
    flow = service.ask(GetFlowQuery(flow_id=flow_id))
    if flow is None and not flow_id.startswith("flow-"):
        flow = service.ask(GetFlowQuery(flow_id=f"flow-{flow_id}"))
    if flow is None:
        return {}
    options = getattr(flow, "options", None) or {}
    if not isinstance(options, dict):
        return {}
    metadata = options.get("metadata") or {}
    if not isinstance(metadata, dict):
        return {}
    assist = metadata.get("assist") or {}
    return assist if isinstance(assist, dict) else {}


def answers_from_view(view: dict[str, Any]) -> dict[str, Any]:
    answers = view.get("answers")
    if isinstance(answers, dict):
        return answers
    pattern = view.get("pattern")
    if isinstance(pattern, dict):
        nested = pattern.get("answers")
        if isinstance(nested, dict):
            return nested
    return {}


__all__ = [
    "answers_from_view",
    "assist_metadata",
    "assist_metadata_from_view",
    "flow_id_from_view",
    "scenario_id_from_view",
]
