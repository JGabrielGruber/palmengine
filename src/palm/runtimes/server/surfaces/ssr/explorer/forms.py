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


def assist_start_form(scenario_id: str) -> str:
    """POST form to start an assist scenario session."""
    action = f"/explorer/assist/scenarios/{escape(scenario_id)}/start"
    return (
        f'<form class="schema-form" action="{action}" method="POST">'
        '<p class="muted">Starts a new assist session and opens the assistant workspace.</p>'
        '<div class="form-actions">'
        '<button class="btn-primary" type="submit">Start assist session</button>'
        "</div></form>"
    )


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
        f"Prefer registered flows above, or use <code>POST /v1/api/flows/{{flow_id}}/create</code> for full payloads.</p>"
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


def wizard_resource_form(
    instance_id: str,
    prompt: Mapping[str, Any],
    *,
    htmx: bool = True,
) -> str:
    """Non-interactive resource step — auto-tick or child-wait, never free-text input."""
    prompt_text = prompt.get("text") or prompt.get("prompt")
    prompt_html = (
        f'<p class="wizard-prompt-text">{escape(str(prompt_text))}</p>' if prompt_text else ""
    )

    validation = prompt.get("validation_error")
    validation_html = ""
    if validation:
        validation_html = f'<p class="wizard-validation">{escape(str(validation))}</p>'

    resource_error = prompt.get("resource_error")
    if resource_error:
        validation_html += f'<p class="wizard-validation">{escape(str(resource_error))}</p>'

    if prompt.get("waiting_for_child"):
        child_job_id = prompt.get("waiting_for_child_job_id") or "child"
        child_instance_id = prompt.get("waiting_for_child_instance_id")
        child_status = prompt.get("child_status") or "WAITING_FOR_INPUT"
        child_instance_href = prompt.get("child_instance_href")
        if not child_instance_href and child_instance_id:
            child_instance_href = f"/explorer/instances/{child_instance_id}"
        child_job_href = prompt.get("child_job_href")
        if not child_job_href and child_job_id:
            child_job_href = f"/explorer/jobs/{child_job_id}"

        child_link = ""
        if child_instance_href:
            child_link = (
                f'<p class="resource-child-link">'
                f'<a class="btn-primary" href="{escape(str(child_instance_href))}">'
                f"Open nested wizard"
                f"</a>"
            )
            if child_job_href:
                child_link += (
                    f' <a class="btn-default" href="{escape(str(child_job_href))}">'
                    f"View child job</a>"
                )
            child_link += "</p>"

        body = (
            f"{prompt_html}{validation_html}"
            f'<p class="muted">Nested wizard <code>{escape(str(child_job_id))}</code> '
            f"is {escape(str(child_status))}. Complete it in a separate tab, then return here "
            f"(this page auto-refreshes while waiting).</p>"
            f"{child_link}"
        )
        resume_action = f"/explorer/instances/{instance_id}/resume-child-wait"
        htmx_attrs = _wizard_htmx_attrs(resume_action) if htmx else ""
        auto_poll = ' hx-trigger="load, every 3s"' if htmx else ""
        toolbar = (
            f'<form class="resource-step-form resume-child-wait" action="{escape(resume_action)}" '
            f'method="POST"{htmx_attrs}{auto_poll}>'
            f'<button class="btn-default" type="submit">Check nested wizard status</button>'
            f"{_wizard_loading_indicator()}"
            f"</form>"
        )
        return (
            f'<div class="resource-step-panel" role="region" aria-live="polite">'
            f"{body}{toolbar}</div>"
        )

    resume_action = f"/explorer/instances/{instance_id}/resume-wizard-tick"
    htmx_attrs = _wizard_htmx_attrs(resume_action) if htmx else ""
    auto_trigger = ' hx-trigger="load"' if htmx else ""
    body = (
        f"{prompt_html}{validation_html}"
        '<p class="muted">Resource steps run automatically — launching the nested flow now.</p>'
    )
    toolbar = (
        f'<form class="resource-step-form resume-wizard-tick" action="{escape(resume_action)}" '
        f'method="POST"{htmx_attrs}{auto_trigger}>'
        f'<button class="btn-primary" type="submit">Launch flow</button>'
        f"{_wizard_loading_indicator()}"
        f"</form>"
    )
    return (
        f'<div class="resource-step-panel" role="region" aria-live="polite">{body}{toolbar}</div>'
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
    if prompt.get("step_kind") == "collection" or prompt.get("collection_phase"):
        from palm.runtimes.server.surfaces.ssr.explorer.components import collection_form

        return collection_form(instance_id, dict(prompt))

    if prompt.get("step_kind") == "resource" or prompt.get("field_type") == "resource":
        return wizard_resource_form(instance_id, prompt, htmx=htmx)

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

    htmx_attrs = _wizard_htmx_attrs(action) if htmx else ""

    choice_buttons = _wizard_choice_buttons(prompt, htmx=htmx, action=action)

    return (
        f'<form class="schema-form wizard-input-form" action="{escape(action)}" method="POST"{htmx_attrs}>'
        f"{error_html}{validation_html}{prompt_html}"
        f"{choice_buttons}"
        f'<div class="form-field">'
        f'<label for="value">{escape(label)}</label>'
        f"{field_html}"
        f"</div>"
        f'<div class="form-actions">'
        f'<button class="btn-primary" type="submit">Submit input</button>'
        f"{_wizard_loading_indicator()}"
        f"</div>"
        f"</form>"
    )


def collection_action_form(
    instance_id: str,
    action: str,
    *,
    item_index: int | None = None,
    label: str,
    tone: str = "primary",
    value: str | None = None,
) -> str:
    """Compact HTMX button form for collection menu actions."""
    post_action = f"/explorer/instances/{instance_id}/input"
    hidden = f'<input type="hidden" name="collection_action" value="{escape(action)}" />'
    if item_index is not None:
        hidden += f'<input type="hidden" name="item_index" value="{item_index}" />'
    if value is not None:
        hidden += f'<input type="hidden" name="value" value="{escape(value)}" />'
    btn_class = "btn-primary" if tone == "primary" else f"btn btn-{escape(tone)}"
    if tone == "ghost":
        btn_class = "btn-ghost"
    elif tone == "danger":
        btn_class = "btn-danger"
    return (
        f'<form class="collection-action-form" action="{escape(post_action)}" method="POST"'
        f'{_wizard_htmx_attrs(post_action)} role="group" aria-label="{escape(label)}">'
        f"{hidden}"
        f'<button type="submit" class="{btn_class}" aria-label="{escape(label)}">'
        f"{escape(label)}</button>"
        f"</form>"
    )


def collection_field_form(instance_id: str, prompt: Mapping[str, Any]) -> str:
    """Sequential item field input during add/edit."""
    action = f"/explorer/instances/{instance_id}/input"
    label = prompt.get("title") or prompt.get("text") or "Value"
    pattern = {
        "field_type": prompt.get("field_type"),
        "effective_schema_type": prompt.get("effective_schema_type"),
        "choices": prompt.get("choices"),
    }
    field_html = _render_job_value_field(pattern, None)

    prompt_text = prompt.get("text")
    prompt_html = f'<p class="wizard-prompt-text">{escape(prompt_text)}</p>' if prompt_text else ""

    validation = prompt.get("validation_error")
    validation_html = ""
    if validation:
        validation_html = f'<p class="wizard-validation">{escape(str(validation))}</p>'

    progress = prompt.get("collection_progress")
    progress_html = ""
    if progress:
        progress_html = f'<p class="collection-field-progress">{escape(str(progress))}</p>'

    draft = prompt.get("collection_draft")
    draft_html = ""
    if isinstance(draft, dict) and draft:
        rows = []
        for key, val in draft.items():
            rows.append(f"<dt>{escape(str(key))}</dt><dd>{escape(str(val))}</dd>")
        draft_html = (
            f'<div class="collection-draft-panel">'
            f"<h4>Draft so far</h4>"
            f'<dl class="definition-dl">{"".join(rows)}</dl>'
            f"</div>"
        )

    choice_buttons = _wizard_choice_buttons(prompt, htmx=True, action=action)
    cancel_btn = collection_action_form(instance_id, "cancel", label="Cancel", tone="ghost")
    has_choices = bool(_normalize_choices(prompt.get("choices")))
    value_field = ""
    if not has_choices:
        value_field = (
            f'<div class="form-field">'
            f'<label for="value">{escape(str(label))}</label>'
            f"{field_html}"
            f"</div>"
        )

    return (
        f'<div class="collection-field-panel" role="region" aria-label="Item field input">'
        f"{progress_html}{draft_html}"
        f'<form class="schema-form wizard-input-form collection-field-form" '
        f'action="{escape(action)}" method="POST"{_wizard_htmx_attrs(action)}>'
        f"{validation_html}{prompt_html}"
        f"{choice_buttons}"
        f"{value_field}"
        f'<div class="form-actions">'
        f'<button class="btn-primary" type="submit">Save field</button>'
        f"{_wizard_loading_indicator()}"
        f"</div>"
        f"</form>"
        f'<div class="form-actions" style="margin-top:0.5rem">{cancel_btn}</div>'
        f"</div>"
    )


def collection_remove_form(instance_id: str, prompt: Mapping[str, Any]) -> str:
    """Confirm removal with item preview."""
    from palm.runtimes.server.surfaces.ssr.explorer.components import (
        _collection_item_field_lines,
        _collection_item_title,
    )

    index = prompt.get("collection_remove_index")
    items = prompt.get("collection_items") or []
    preview_html = '<p class="muted">Item preview unavailable.</p>'
    if isinstance(index, int) and isinstance(items, list) and 0 <= index < len(items):
        item = items[index]
        if isinstance(item, dict):
            label_field = prompt.get("label_field")
            item_fields = prompt.get("item_fields")
            field_specs = list(item_fields) if isinstance(item_fields, list) else None
            title = _collection_item_title(item, index, label_field, field_specs)
            lines = _collection_item_field_lines(item, label_field, field_specs)
            body = f"<strong>{escape(title)}</strong>"
            if lines:
                body += f'<div class="item-fields">{"<br>".join(lines)}</div>'
            preview_html = f'<div class="collection-remove-preview">{body}</div>'

    prompt_text = prompt.get("text")
    prompt_html = f'<p class="wizard-prompt-text">{escape(prompt_text)}</p>' if prompt_text else ""

    validation = prompt.get("validation_error")
    validation_html = ""
    if validation:
        validation_html = f'<p class="wizard-validation">{escape(str(validation))}</p>'

    return (
        f'<div class="collection-remove-confirm" role="alertdialog" aria-labelledby="collection-remove-title">'
        f'<h4 id="collection-remove-title">Confirm removal</h4>'
        f"{prompt_html}{validation_html}"
        f"{preview_html}"
        f'<div class="form-actions" style="margin-top:1rem">'
        f'{collection_action_form(instance_id, "confirm_remove", label="Yes, remove", tone="danger", value="yes")}'
        f'{collection_action_form(instance_id, "confirm_remove", label="No, keep it", tone="ghost", value="no")}'
        f'{_wizard_loading_indicator()}'
        f"</div>"
        f"</div>"
    )


def collection_select_form(instance_id: str, prompt: Mapping[str, Any]) -> str:
    """Fallback select-item UI when compound edit/remove is not used."""
    from palm.runtimes.server.surfaces.ssr.explorer.components import collection_list

    action_label = prompt.get("collection_select_action") or "edit"
    title = "Select item to edit" if action_label == "edit" else "Select item to remove"
    prompt_text = prompt.get("text")
    prompt_html = f'<p class="wizard-prompt-text">{escape(prompt_text)}</p>' if prompt_text else ""

    validation = prompt.get("validation_error")
    validation_html = ""
    if validation:
        validation_html = f'<p class="wizard-validation">{escape(str(validation))}</p>'

    return (
        f'<div class="collection-select-panel" role="region" aria-label="{escape(str(title))}">'
        f"<h4>{escape(str(title))}</h4>"
        f"{prompt_html}{validation_html}"
        f'{collection_list(instance_id, dict(prompt), action="select")}'
        f'<div class="collection-toolbar">'
        f'{collection_action_form(instance_id, "cancel", label="Cancel", tone="ghost")}'
        f'{_wizard_loading_indicator()}'
        f"</div>"
        f"</div>"
    )


def _wizard_htmx_attrs(action: str) -> str:
    return (
        f' hx-post="{escape(action)}"'
        ' hx-target="#wizard-workspace"'
        ' hx-swap="outerHTML"'
        ' hx-indicator="#wizard-loading"'
        ' hx-disabled-elt="button, input, select, textarea"'
    )


def _wizard_loading_indicator() -> str:
    return (
        '<span id="wizard-loading" class="htmx-indicator wizard-loading" '
        'role="status" aria-live="polite" aria-atomic="true">Updating…</span>'
    )


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
    htmx_attrs = _wizard_htmx_attrs(action) if htmx else ""
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
    from palm.common.operator.input_coercion import coerce_job_input as _coerce

    return _coerce(raw, pattern)


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
