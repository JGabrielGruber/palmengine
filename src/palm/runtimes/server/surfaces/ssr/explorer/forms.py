"""Schema-driven HTML forms for Palm Explorer."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from palm.common.runtimes.server.ssr.render import escape
from palm.core.context.state_schema import DictStateSchema
from palm.runtimes.server.surfaces.ssr.explorer.schemas import build_flow_submit_schema

if TYPE_CHECKING:
    from palm.definitions.flow import FlowDefinition


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


def flow_submit_form(
    flows: list[FlowDefinition],
    *,
    action: str = "/explorer/flows/submit",
    selected_flow_id: str | None = None,
    values: Mapping[str, Any] | None = None,
    errors: list[str] | None = None,
) -> str:
    """Render a context-aware flow submission form with a registered-flow dropdown."""
    current = dict(values or {})
    if selected_flow_id and not current.get("flow_id"):
        current["flow_id"] = selected_flow_id

    schema = build_flow_submit_schema(flows)
    props = _schema_properties(schema)
    selected = str(current.get("flow_id") or "")
    selected_flow = _find_flow(flows, selected)
    prefill_note = ""
    if selected_flow:
        prefill_note = (
            f'<p class="muted">Pre-selected: <strong>{escape(selected_flow.name)}</strong> '
            f"— review and click <strong>Start this flow</strong>.</p>"
        )

    error_html = ""
    if errors:
        items = "".join(f"<li>{escape(error)}</li>" for error in errors)
        error_html = f'<div class="alert alert-error"><ul class="form-errors">{items}</ul></div>'

    flow_field = _render_flow_select(flows, selected=selected)
    context_panel = _flow_context_panel(selected_flow) if selected_flow else ""
    job_spec = props.get("job_id", {})
    job_field = _render_field(
        "job_id",
        job_spec if isinstance(job_spec, dict) else {},
        current.get("job_id", ""),
    )
    advanced_job_field = _render_field(
        "job_id",
        {**(job_spec if isinstance(job_spec, dict) else {}), "title": "Job ID (optional)"},
        current.get("job_id", ""),
        field_id="job_id_advanced",
    )

    registered_form = (
        f'<form class="schema-form flow-submit-form flow-submit-primary" action="{escape(action)}" method="POST">'
        f"{error_html}"
        f'<input type="hidden" name="submit_mode" value="registered" />'
        f"{prefill_note}"
        f"{flow_field}"
        f"{context_panel}"
        f"{job_field}"
        f'<div class="form-actions"><button class="btn-primary" type="submit">Start this flow</button></div>'
        f"</form>"
    )

    wizard_name_spec = props.get("wizard_name", {})
    wizard_steps_spec = props.get("wizard_steps", {})
    advanced_form = (
        f'<form class="schema-form flow-submit-advanced" action="{escape(action)}" method="POST">'
        f'<input type="hidden" name="submit_mode" value="inline_wizard" />'
        f"{_render_field('wizard_name', wizard_name_spec if isinstance(wizard_name_spec, dict) else {}, current.get('wizard_name', ''))}"
        f"{_render_field('wizard_steps', wizard_steps_spec if isinstance(wizard_steps_spec, dict) else {}, current.get('wizard_steps', 2))}"
        f"{advanced_job_field}"
        f'<div class="form-actions">'
        f'<button class="btn-primary" type="submit">Start test wizard</button>'
        f"</div>"
        f"</form>"
    )

    return (
        f'<div class="flow-submit-stack">'
        f"{registered_form}"
        f'<details class="advanced-panel">'
        f"<summary>Advanced: quick test wizard (no registered definition)</summary>"
        f'<p class="muted">For operator experiments only — starts a minimal inline wizard. '
        f"Prefer registered flows above, or use <code>POST /v1/jobs</code> for full payloads.</p>"
        f"{advanced_form}"
        f"</details>"
        f"</div>"
    )


def _find_flow(flows: list[FlowDefinition], flow_id: str) -> FlowDefinition | None:
    for flow in flows:
        if flow.definition_id == flow_id:
            return flow
    return None


def _render_flow_select(flows: list[FlowDefinition], *, selected: str) -> str:
    from palm.runtimes.server.surfaces.ssr.explorer.pages.utils import flow_option_label

    if not flows:
        return (
            '<div class="form-field">'
            '<p class="muted">No flows registered yet. Register a definition or use the advanced test wizard below.</p>'
            "</div>"
        )

    options = ['<option value="">Choose a flow…</option>']
    for flow in flows:
        flow_id = flow.definition_id
        is_selected = " selected" if flow_id == selected else ""
        label = flow_option_label(flow)
        options.append(f'<option value="{escape(flow_id)}"{is_selected}>{escape(label)}</option>')
    body = "".join(options)
    return (
        '<div class="form-field">'
        '<label for="flow_id">Registered flow</label>'
        f'<select id="flow_id" name="flow_id" required>{body}</select>'
        '<span class="field-hint">Name · pattern · description. Tip: use <strong>Start</strong> on the flow catalog to pre-fill.</span>'
        "</div>"
    )


def _flow_context_panel(flow: FlowDefinition) -> str:
    from palm.runtimes.server.surfaces.ssr.explorer.components import badge
    from palm.runtimes.server.surfaces.ssr.explorer.pages.utils import flow_description

    schema_badge = (
        badge("schema", tone="default")
        if flow.has_state_schema
        else badge("no schema", tone="default")
    )
    return (
        '<div class="flow-context-panel panel">'
        f"<p>{badge(flow.pattern)} {schema_badge}</p>"
        f'<p class="muted">{escape(flow_description(flow))}</p>'
        f'<p class="muted">Definition id: <code>{escape(flow.definition_id)}</code></p>'
        "</div>"
    )


def resource_invoke_form(
    resource_id: str,
    payload: Mapping[str, Any],
    *,
    action: str | None = None,
    values: Mapping[str, Any] | None = None,
    state_json: str = "",
    errors: list[str] | None = None,
    binding_rows: list[tuple[str, str]] | None = None,
    result: Any | None = None,
) -> str:
    """Interactive Try Invoke form for Explorer resource detail."""
    current = dict(values or {})
    error_html = ""
    if errors:
        items = "".join(f"<li>{escape(error)}</li>" for error in errors)
        error_html = f'<div class="alert alert-error"><ul class="form-errors">{items}</ul></div>'

    param_keys = payload.get("param_keys") or list((payload.get("params") or {}).keys())
    fields: list[str] = []
    params_spec = payload.get("params") or {}
    for key in param_keys:
        raw_default = params_spec.get(key, "") if isinstance(params_spec, dict) else ""
        fields.append(
            _render_field(
                str(key),
                {
                    "type": "string",
                    "title": str(key),
                    "description": f"Binding template: {raw_default}" if raw_default else "",
                },
                current.get(key, ""),
            )
        )

    resource_id_value = current.get("resource_id", payload.get("resource_id") or "")
    fields.insert(
        0,
        _render_field(
            "resource_id",
            {"type": "string", "title": "Resource ID", "description": "Optional override"},
            resource_id_value,
        ),
    )

    action_value = current.get("action", action or payload.get("action") or "fetch")
    fields.insert(
        0,
        _render_field(
            "action",
            {"type": "string", "title": "Action", "description": "Provider action to invoke"},
            action_value,
        ),
    )

    state_text = state_json or current.get("state_json") or "{}"
    binding_html = ""
    if binding_rows:
        rows = "".join(
            f"<tr><td>{escape(key)}</td><td><code>{escape(value)}</code></td></tr>"
            for key, value in binding_rows
        )
        binding_html = (
            '<div class="binding-preview panel">'
            "<h4>State binding preview</h4>"
            f'<table class="data-table"><tbody>{rows}</tbody></table>'
            "</div>"
        )

    result_html = ""
    if result is not None:
        from palm.runtimes.server.surfaces.ssr.explorer.components import code_block

        result_html = (
            '<div class="panel invoke-result">'
            "<h4>Invoke result</h4>"
            f"{code_block(result)}"
            "</div>"
        )

    post_action = f"/explorer/resources/{escape(resource_id)}/invoke"
    return (
        f'<form class="schema-form resource-invoke-form" action="{post_action}" method="POST">'
        f"{error_html}"
        f"{result_html}"
        f"{binding_html}"
        f'{"".join(fields)}'
        '<div class="form-field">'
        '<label for="state_json">State (JSON)</label>'
        f'<textarea id="state_json" name="state_json" rows="5" '
        f'placeholder="{{&quot;customer_id&quot;: &quot;42&quot;}}">{escape(state_text)}</textarea>'
        '<span class="field-hint">Used to resolve <code>{{ state.key }}</code> placeholders in params.</span>'
        "</div>"
        '<div class="form-actions">'
        '<button class="btn-primary" type="submit">Invoke resource</button>'
        "</div>"
        "</form>"
    )


def wizard_input_form(
    instance_id: str,
    prompt: Mapping[str, Any],
    *,
    value: Any = None,
    errors: list[str] | None = None,
    htmx: bool = True,
) -> str:
    """Interactive wizard input with optional HTMX partial updates."""
    action = f"/explorer/instances/{instance_id}/input"
    label = prompt.get("title") or prompt.get("text") or "Value"
    pattern = {
        "prompt": prompt.get("text"),
        "prompt_title": prompt.get("title"),
        "field_type": prompt.get("field_type"),
        "effective_schema_type": prompt.get("effective_schema_type"),
        "choices": prompt.get("choices"),
        "collection_phase": prompt.get("collection_phase"),
    }
    field_html = _render_job_value_field(pattern, value)
    error_html = ""
    if errors:
        items = "".join(f"<li>{escape(error)}</li>" for error in errors)
        error_html = f'<div class="alert alert-error"><ul class="form-errors">{items}</ul></div>'

    prompt_text = prompt.get("text")
    prompt_html = f'<p class="wizard-prompt-text">{escape(prompt_text)}</p>' if prompt_text else ""

    validation = prompt.get("validation_error")
    validation_html = ""
    if validation:
        validation_html = f'<p class="wizard-validation">{escape(str(validation))}</p>'

    collection_html = _wizard_collection_hint(prompt)

    htmx_attrs = ""
    if htmx:
        htmx_attrs = (
            f' hx-post="{escape(action)}"'
            ' hx-target="#wizard-workspace"'
            ' hx-swap="outerHTML"'
            ' hx-indicator="#wizard-loading"'
        )

    choice_buttons = _wizard_choice_buttons(prompt, htmx=htmx, action=action)

    return (
        f'<form class="schema-form wizard-input-form" action="{escape(action)}" method="POST"{htmx_attrs}>'
        f"{error_html}{validation_html}{prompt_html}{collection_html}"
        f"{choice_buttons}"
        f'<div class="form-field">'
        f'<label for="value">{escape(label)}</label>'
        f"{field_html}"
        f"</div>"
        f'<div class="form-actions">'
        f'<button class="btn-primary" type="submit">Submit input</button>'
        f'<span id="wizard-loading" class="htmx-indicator wizard-loading">Updating…</span>'
        f"</div>"
        f"</form>"
    )


def _wizard_collection_hint(prompt: Mapping[str, Any]) -> str:
    phase = prompt.get("collection_phase")
    items = prompt.get("collection_items")
    if not phase and not items:
        return ""
    parts = []
    if phase:
        parts.append(f"Phase: <strong>{escape(str(phase))}</strong>")
    if isinstance(items, list) and items:
        rows = []
        for item in items:
            if isinstance(item, dict):
                label = item.get("label") or item.get("id") or str(item)
            else:
                label = str(item)
            rows.append(f"<li>{escape(str(label))}</li>")
        parts.append(f'<ul class="collection-items">{"".join(rows)}</ul>')
    return f'<div class="collection-panel muted-section">{"".join(parts)}</div>'


def _wizard_choice_buttons(
    prompt: Mapping[str, Any],
    *,
    htmx: bool,
    action: str,
) -> str:
    choices = _normalize_choices(prompt.get("choices"))
    field_type = prompt.get("field_type")
    if field_type != "choice" or not choices:
        return ""
    buttons = []
    htmx_attrs = ""
    if htmx:
        htmx_attrs = (
            f' hx-post="{escape(action)}"'
            ' hx-target="#wizard-workspace"'
            ' hx-swap="outerHTML"'
            ' hx-indicator="#wizard-loading"'
        )
    for choice in choices:
        buttons.append(
            f'<form class="wizard-choice-form" action="{escape(action)}" method="POST"{htmx_attrs}>'
            f'<input type="hidden" name="value" value="{escape(str(choice))}" />'
            f'<button type="submit" class="wizard-choice-btn">{escape(str(choice))}</button>'
            f"</form>"
        )
    return f'<div class="wizard-choice-grid" role="group" aria-label="Choices">{"".join(buttons)}</div>'


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


def _normalize_choices(choices: object | None) -> list[Any]:
    """Return a safe iterable for choice fields (never None)."""
    if choices is None:
        return []
    if isinstance(choices, list):
        return choices
    if isinstance(choices, tuple | set):
        return list(choices)
    return []


def _schema_properties(schema: DictStateSchema) -> dict[str, Any]:
    props = schema.definition.get("properties", {})
    return dict(props) if isinstance(props, dict) else {}


def _render_field(
    key: str,
    spec: Mapping[str, Any],
    value: Any,
    *,
    field_id: str | None = None,
) -> str:
    if not spec:
        spec = {}
    field_type = spec.get("type", "string")
    label = spec.get("title", key.replace("_", " ").title())
    required = key in spec.get("required", []) or key in (spec.get("parent_required") or [])
    req_attr = " required" if required else ""
    element_id = escape(field_id or key)
    display = escape(value) if value is not None else ""

    enum_values = spec.get("enum")
    if isinstance(enum_values, list) and enum_values:
        options = []
        placeholder = spec.get("x-placeholder")
        if placeholder:
            selected = " selected" if not value else ""
            options.append(f'<option value=""{selected}>{escape(placeholder)}</option>')
        for item in enum_values:
            selected = " selected" if str(item) == str(value) else ""
            options.append(f'<option value="{escape(item)}"{selected}>{escape(item)}</option>')
        control = (
            f'<select id="{element_id}" name="{escape(key)}"{req_attr}>{"".join(options)}</select>'
        )
    elif field_type == "boolean":
        checked = " checked" if str(value).lower() in {"true", "1", "yes", "on"} else ""
        control = f'<input type="checkbox" id="{element_id}" name="{escape(key)}" value="true"{checked}{req_attr} />'
    elif field_type in {"integer", "number"}:
        step = "1" if field_type == "integer" else "any"
        control = (
            f'<input type="number" id="{element_id}" name="{escape(key)}" value="{display}" '
            f'step="{step}"{req_attr} />'
        )
    elif field_type in {"object", "array"}:
        text = display if display else "{}"
        control = (
            f'<textarea id="{element_id}" name="{escape(key)}" rows="4"{req_attr}>{text}</textarea>'
        )
    else:
        control = f'<input type="text" id="{element_id}" name="{escape(key)}" value="{display}"{req_attr} />'

    hint = spec.get("description")
    hint_html = f'<span class="field-hint">{escape(hint)}</span>' if hint else ""
    return (
        f'<div class="form-field">'
        f'<label for="{element_id}">{escape(label)}</label>'
        f"{control}{hint_html}"
        f"</div>"
    )


def _render_job_value_field(pattern: Mapping[str, Any], value: Any) -> str:
    field_type = pattern.get("field_type")
    schema_type = pattern.get("effective_schema_type")
    choices = _normalize_choices(pattern.get("choices"))
    display = escape(value) if value is not None else ""

    if field_type == "choice" and choices:
        options = []
        for item in choices:
            selected = " selected" if str(item) == str(value) else ""
            options.append(f'<option value="{escape(item)}"{selected}>{escape(item)}</option>')
        return f'<select id="value" name="value" required>{"".join(options)}</select>'

    if field_type == "choice" and not choices:
        return (
            f'<input type="text" id="value" name="value" value="{display}" required />'
            '<span class="field-hint">No choices configured for this step — enter a value.</span>'
        )

    if field_type == "confirm" or schema_type == "boolean":
        checked = " checked" if str(value).lower() in {"true", "1", "yes", "on"} else ""
        return f'<input type="checkbox" id="value" name="value" value="true"{checked} />'

    if schema_type == "integer":
        return (
            f'<input type="number" id="value" name="value" value="{display}" step="1" required />'
        )
    if schema_type == "number":
        return (
            f'<input type="number" id="value" name="value" value="{display}" step="any" required />'
        )

    return f'<input type="text" id="value" name="value" value="{display}" required />'
