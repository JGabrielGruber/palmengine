"""Portal-friendly structured input schema (chat profile)."""

from __future__ import annotations

from typing import Any

from palm.services.assist.present.status import human_status


def resolve_field_required(composed: dict[str, Any]) -> bool:
    """Prefer active collection field required over parent step required."""
    active = composed.get("collection_field")
    item_fields = composed.get("item_fields")
    if active and isinstance(item_fields, list):
        for field in item_fields:
            if not isinstance(field, dict):
                continue
            if str(field.get("slug") or "") == str(active):
                if "required" in field:
                    return bool(field.get("required"))
                break
    if "required" in composed:
        return bool(composed.get("required"))
    return True


def widget_for_field(field_type: str, *, step_kind: str) -> str:
    if step_kind in {"summary", "commit"} or field_type == "confirm":
        return "confirm"
    if field_type == "choice":
        return "choice"
    if step_kind == "collection":
        return "collection"
    return "text"


def build_input_schema(
    composed: dict[str, Any],
    *,
    choices: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """Build Portal-friendly input schema for the active step."""
    status = human_status(composed.get("status"))
    if status not in {"waiting", "running"}:
        if status in {"complete", "failed", "catalog", "ok"}:
            step_kind = composed.get("step_kind")
            if step_kind not in {"input", "collection", "summary", "commit", None}:
                return None
            if status in {"complete", "failed"}:
                return None

    field_type = composed.get("field_type")
    step_kind = composed.get("step_kind") or "input"
    if not field_type and step_kind in {"resource", "transform", "branch"}:
        schema: dict[str, Any] = {
            "kind": step_kind,
            "step": composed.get("step") or composed.get("slug"),
            "interactive": False,
        }
        if composed.get("resource_ref"):
            schema["resource_ref"] = composed["resource_ref"]
        return schema

    if not field_type and not choices and step_kind not in {"collection", "summary", "commit"}:
        if status == "waiting":
            field_type = "text"
        else:
            return None

    widget = widget_for_field(str(field_type or "text"), step_kind=str(step_kind))
    required = resolve_field_required(composed)
    schema = {
        "kind": "field",
        "step": composed.get("step") or composed.get("slug"),
        "step_index": composed.get("step_index"),
        "step_kind": step_kind,
        "field_type": field_type or "text",
        "widget": widget,
        "required": required,
        "title": composed.get("prompt_title"),
        "prompt": composed.get("prompt"),
        "interactive": True,
    }
    if choices:
        schema["choices"] = choices
    rules = composed.get("validation_rules")
    if isinstance(rules, list) and rules:
        schema["validation"] = rules
    if step_kind == "collection" or composed.get("collection_phase"):
        schema["kind"] = "collection"
        schema["collection_phase"] = composed.get("collection_phase")
        schema["collection_field"] = composed.get("collection_field")
        if composed.get("item_fields") is not None:
            schema["item_fields"] = composed["item_fields"]
        if composed.get("collection_key") is not None:
            schema["collection_key"] = composed["collection_key"]
        if composed.get("min_items") is not None:
            schema["min_items"] = composed["min_items"]
        if composed.get("label_field") is not None:
            schema["label_field"] = composed["label_field"]
        if required is False and composed.get("collection_phase") == "field":
            schema["skip_allowed"] = True
            schema["skip_value"] = ""
            schema["skip_label"] = "Skip"
    if composed.get("validation_error"):
        schema["error"] = composed["validation_error"]
    return {k: v for k, v in schema.items() if v is not None}


__all__ = [
    "build_input_schema",
    "resolve_field_required",
    "widget_for_field",
]
