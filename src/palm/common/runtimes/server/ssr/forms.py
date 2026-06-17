"""Schema-driven HTML forms for Palm Explorer."""

from __future__ import annotations

import json
from typing import Any, Mapping

from palm.common.runtimes.server.ssr.render import escape
from palm.core.context.state_schema import DictStateSchema


def alert(message: str, *, tone: str = "success") -> str:
    """Render a dismissible-style notice banner."""
    return f'<div class="alert alert-{escape(tone)}">{escape(message)}</div>'


def schema_form(
    schema: DictStateSchema,
    *,
    action: str,
    method: str = "POST",
    values: Mapping[str, Any] | None = None,
    errors: list[str] | None = None,
    submit_label: str = "Submit",
    hidden_fields: Mapping[str, str] | None = None,
) -> str:
    """Render an HTML form from a :class:`DictStateSchema` object schema."""
    current = dict(values or {})
    fields: list[str] = []
    for key, spec in schema.definition.get("properties", {}).items():
        if not isinstance(spec, dict):
            continue
        fields.append(_render_field(key, spec, current.get(key, spec.get("default", ""))))

    error_html = ""
    if errors:
        items = "".join(f"<li>{escape(error)}</li>" for error in errors)
        error_html = f'<div class="alert alert-error"><ul class="form-errors">{items}</ul></div>'

    hidden_html = ""
    for key, value in (hidden_fields or {}).items():
        hidden_html += f'<input type="hidden" name="{escape(key)}" value="{escape(value)}" />'

    return (
        f'<form class="schema-form" action="{escape(action)}" method="{escape(method)}">'
        f"{error_html}{hidden_html}"
        f'{"".join(fields)}'
        f'<div class="form-actions"><button class="btn-primary" type="submit">{escape(submit_label)}</button></div>'
        f"</form>"
    )


def job_input_form(
    job_id: str,
    pattern: Mapping[str, Any],
    *,
    value: Any = None,
    errors: list[str] | None = None,
) -> str:
    """Render a single-value input form for interactive wizard jobs."""
    action = f"/explorer/jobs/{job_id}/input"
    label = pattern.get("prompt_title") or pattern.get("prompt") or "Value"
    field_html = _render_job_value_field(pattern, value)
    error_html = ""
    if errors:
        items = "".join(f"<li>{escape(error)}</li>" for error in errors)
        error_html = f'<div class="alert alert-error"><ul class="form-errors">{items}</ul></div>'
    prompt = pattern.get("prompt")
    prompt_html = f'<p class="muted">{escape(prompt)}</p>' if prompt else ""
    return (
        f'<form class="schema-form job-input-form" action="{escape(action)}" method="POST">'
        f"{error_html}{prompt_html}"
        f'<div class="form-field">'
        f'<label for="value">{escape(label)}</label>'
        f"{field_html}"
        f"</div>"
        f'<div class="form-actions"><button class="btn-primary" type="submit">Provide input</button></div>'
        f"</form>"
    )


def parse_form_values(
    schema: DictStateSchema,
    form_data: Mapping[str, Any],
) -> tuple[dict[str, Any], list[str]]:
    """Coerce and validate posted form fields against a schema."""
    coerced = _coerce_object_fields(schema, form_data)
    errors = schema.validate_state(coerced)
    return coerced, errors


def coerce_job_input(raw: str, pattern: Mapping[str, Any]) -> Any:
    """Coerce a posted job input string to the expected Python value."""
    field_type = pattern.get("field_type")
    schema_type = pattern.get("effective_schema_type")

    if field_type == "choice":
        return raw
    if field_type == "confirm":
        return raw.lower() in {"true", "1", "yes", "on"}
    if schema_type == "integer":
        return int(raw)
    if schema_type == "number":
        return float(raw)
    if schema_type == "boolean":
        return raw.lower() in {"true", "1", "yes", "on"}

    choices = pattern.get("choices")
    if isinstance(choices, list) and raw in [str(item) for item in choices]:
        return raw

    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return raw


def _coerce_object_fields(schema: DictStateSchema, form_data: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    properties = schema.definition.get("properties", {})
    if not isinstance(properties, dict):
        return result
    for key, spec in properties.items():
        if key not in form_data:
            continue
        raw = form_data[key]
        if not isinstance(spec, dict):
            result[key] = raw
            continue
        result[key] = _coerce_field_value(str(raw), spec)
    return result


def _coerce_field_value(raw: str, spec: Mapping[str, Any]) -> Any:
    field_type = spec.get("type")
    if field_type == "integer":
        return int(raw) if raw else 0
    if field_type == "number":
        return float(raw) if raw else 0.0
    if field_type == "boolean":
        return raw.lower() in {"true", "1", "yes", "on"}
    if field_type == "object" or field_type == "array":
        if not raw:
            return {} if field_type == "object" else []
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw
    return raw


def _render_field(key: str, spec: Mapping[str, Any], value: Any) -> str:
    field_type = spec.get("type", "string")
    label = spec.get("title", key.replace("_", " ").title())
    required = key in spec.get("required", []) or key in (spec.get("parent_required") or [])
    req_attr = " required" if required else ""
    field_id = escape(key)
    display = escape(value) if value is not None else ""

    if "enum" in spec and isinstance(spec["enum"], list):
        options = []
        for item in spec["enum"]:
            selected = " selected" if str(item) == str(value) else ""
            options.append(f'<option value="{escape(item)}"{selected}>{escape(item)}</option>')
        control = f'<select id="{field_id}" name="{field_id}"{req_attr}>{"".join(options)}</select>'
    elif field_type == "boolean":
        checked = " checked" if str(value).lower() in {"true", "1", "yes", "on"} else ""
        control = f'<input type="checkbox" id="{field_id}" name="{field_id}" value="true"{checked}{req_attr} />'
    elif field_type in {"integer", "number"}:
        step = "1" if field_type == "integer" else "any"
        control = (
            f'<input type="number" id="{field_id}" name="{field_id}" value="{display}" '
            f'step="{step}"{req_attr} />'
        )
    elif field_type in {"object", "array"}:
        text = display if display else "{}"
        control = (
            f'<textarea id="{field_id}" name="{field_id}" rows="4"{req_attr}>{text}</textarea>'
        )
    else:
        control = f'<input type="text" id="{field_id}" name="{field_id}" value="{display}"{req_attr} />'

    hint = spec.get("description")
    hint_html = f'<span class="field-hint">{escape(hint)}</span>' if hint else ""
    return (
        f'<div class="form-field">'
        f'<label for="{field_id}">{escape(label)}</label>'
        f"{control}{hint_html}"
        f"</div>"
    )


def _render_job_value_field(pattern: Mapping[str, Any], value: Any) -> str:
    field_type = pattern.get("field_type")
    schema_type = pattern.get("effective_schema_type")
    choices = pattern.get("choices")
    display = escape(value) if value is not None else ""

    if field_type == "choice" or (isinstance(choices, list) and choices):
        options = []
        for item in choices:
            selected = " selected" if str(item) == str(value) else ""
            options.append(f'<option value="{escape(item)}"{selected}>{escape(item)}</option>')
        return f'<select id="value" name="value" required>{"".join(options)}</select>'

    if field_type == "confirm" or schema_type == "boolean":
        checked = " checked" if str(value).lower() in {"true", "1", "yes", "on"} else ""
        return f'<input type="checkbox" id="value" name="value" value="true"{checked} />'

    if schema_type == "integer":
        return f'<input type="number" id="value" name="value" value="{display}" step="1" required />'
    if schema_type == "number":
        return f'<input type="number" id="value" name="value" value="{display}" step="any" required />'

    return f'<input type="text" id="value" name="value" value="{display}" required />'