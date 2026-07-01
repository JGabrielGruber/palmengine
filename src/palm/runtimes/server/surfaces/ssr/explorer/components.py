"""SSR HTML components — small composable fragments."""

from __future__ import annotations

from typing import Any

from palm.common.runtimes.server.ssr.render import escape, pretty_json


def _session_api_href(wizard: dict[str, Any], instance_id: str) -> str:
    flow_id = wizard.get("flow_name") or wizard.get("flow_id") or "flow"
    return f"/v1/api/flows/{escape(str(flow_id))}/session/{escape(instance_id)}"


def stat_card(label: str, value: str | int, *, hint: str = "") -> str:
    hint_html = f'<div class="stat-hint">{escape(hint)}</div>' if hint else ""
    return (
        f'<div class="stat-card">'
        f'<div class="stat-value">{escape(value)}</div>'
        f'<div class="stat-label">{escape(label)}</div>'
        f"{hint_html}"
        f"</div>"
    )


def link_card(href: str, title: str, description: str) -> str:
    return (
        f'<a class="link-card" href="{escape(href)}">'
        f"<h3>{escape(title)}</h3>"
        f"<p>{escape(description)}</p>"
        f"</a>"
    )


def data_table(headers: list[str], rows: list[list[str]]) -> str:
    head = "".join(f"<th>{escape(header)}</th>" for header in headers)
    body_rows = []
    for row in rows:
        cells = "".join(f"<td>{cell}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")
    return (
        '<table class="data-table"><thead><tr>'
        f"{head}</tr></thead><tbody>"
        f'{"".join(body_rows)}</tbody></table>'
    )


def code_block(value: Any, *, language: str = "json") -> str:
    return f'<pre class="code-block" data-lang="{escape(language)}"><code>{pretty_json(value)}</code></pre>'


def action_list(actions: list[dict[str, Any]]) -> str:
    if not actions:
        return '<p class="muted">No actions available.</p>'
    items = []
    for action in actions:
        method = escape(action.get("method", "GET"))
        path = escape(action.get("path", "#"))
        label = escape(action.get("action", path))
        description = escape(action.get("description", ""))
        items.append(
            f'<li class="action-item">'
            f'<span class="method">{method}</span> '
            f'<a href="{path}"><code>{path}</code></a> '
            f"<strong>{label}</strong>"
            f'<span class="muted"> — {description}</span>'
            f"</li>"
        )
    return f'<ul class="action-list">{"".join(items)}</ul>'


def event_timeline(events: list[dict[str, Any]]) -> str:
    if not events:
        return '<p class="muted">No recent events.</p>'
    items = []
    for event in events:
        items.append(
            f'<li class="event-item">'
            f'<time>{escape(event.get("recorded_at"))}</time> '
            f'<span class="event-type">{escape(event.get("type"))}</span> '
            f'<span class="muted">{escape(event.get("status") or event.get("current_step") or "")}</span>'
            f"</li>"
        )
    return f'<ul class="event-timeline">{"".join(items)}</ul>'


def badge(text: str, *, tone: str = "default") -> str:
    return f'<span class="badge badge-{escape(tone)}">{escape(text)}</span>'


def action_button(href: str, label: str, *, tone: str = "primary") -> str:
    """Compact call-to-action link styled as a button."""
    return f'<a class="btn btn-{escape(tone)}" href="{escape(href)}">{escape(label)}</a>'


def alert(message: str, *, tone: str = "success") -> str:
    from palm.runtimes.server.surfaces.ssr.explorer import forms

    return forms.alert(message, tone=tone)


def empty_state(title: str, message: str, *, action_href: str = "", action_label: str = "") -> str:
    action_html = ""
    if action_href and action_label:
        action_html = f'<p class="btn-row">{action_button(action_href, action_label)}</p>'
    return (
        '<div class="empty-state">'
        f"<h3>{escape(title)}</h3>"
        f'<p class="muted">{escape(message)}</p>'
        f"{action_html}"
        "</div>"
    )


def catalog_filter_form(
    *,
    action: str,
    providers: list[str],
    selected_provider: str = "",
    query: str = "",
    placeholder: str = "Search resources…",
) -> str:
    options = ['<option value="">All providers</option>']
    for provider in providers:
        selected = " selected" if provider == selected_provider else ""
        options.append(f'<option value="{escape(provider)}"{selected}>{escape(provider)}</option>')
    return (
        f'<form class="catalog-filters" action="{escape(action)}" method="GET">'
        f'<input type="search" name="q" value="{escape(query)}" placeholder="{escape(placeholder)}" '
        f'class="filter-search" aria-label="Search resources" />'
        f'<select name="provider" aria-label="Filter by provider">{"".join(options)}</select>'
        f'<button class="btn btn-primary" type="submit">Filter</button>'
        f'<span class="muted filter-hint">Press <kbd>/</kbd> to focus search</span>'
        f"</form>"
    )


def definition_dl(rows: list[tuple[str, str]]) -> str:
    items = []
    for label, value in rows:
        items.append(f"<dt>{escape(label)}</dt><dd>{escape(value)}</dd>")
    return f'<dl class="definition-dl">{"".join(items)}</dl>'


def action_catalog(actions: list[dict[str, str]]) -> str:
    if not actions:
        return empty_state("No actions", "This provider did not advertise any actions.")
    rows = []
    for action in actions:
        name = action.get("name", "—")
        default = " ★" if action.get("default") else ""
        rows.append(
            [
                f"<strong>{escape(name)}</strong>{default}",
                escape(action.get("description", "")),
            ]
        )
    return data_table(["Action", "Description"], rows)


def resource_timeline_table(entries: list[dict[str, Any]]) -> str:
    if not entries:
        return empty_state(
            "No invocations yet",
            "Resource calls appear here after flows, wizards, or Try Invoke runs.",
        )
    rows = []
    for entry in entries:
        status = (
            "ok" if entry.get("success") else ("fail" if entry.get("success") is False else "—")
        )
        job_cell = "—"
        job_id = entry.get("job_id")
        if job_id:
            job_cell = f'<a href="/explorer/jobs/{escape(str(job_id))}">{escape(str(job_id))}</a>'
        inst_cell = "—"
        instance_id = entry.get("instance_id")
        if instance_id:
            inst_cell = (
                f'<a href="/explorer/instances/{escape(str(instance_id))}">'
                f"{escape(str(instance_id))}</a>"
            )
        rows.append(
            [
                escape(str(entry.get("recorded_at") or "—")),
                escape(str(entry.get("event_type") or "—")),
                escape(str(entry.get("action") or "—")),
                escape(str(entry.get("step_slug") or "—")),
                job_cell,
                inst_cell,
                escape(status),
            ]
        )
    return data_table(
        ["Recorded", "Event", "Action", "Step", "Job", "Instance", "Status"],
        rows,
    )


def invoke_chain(chain: list[dict[str, Any]]) -> str:
    if not chain:
        return '<p class="muted">No compositional invoke chain recorded yet.</p>'
    nodes = []
    for index, node in enumerate(chain):
        label = escape(str(node.get("label") or "invoke"))
        action = node.get("action")
        depth = node.get("depth")
        meta = f"{action}" if action else ""
        if depth is not None:
            meta = f"{meta} · depth {depth}".strip(" ·")
        job_id = node.get("job_id") or node.get("parent_job_id")
        job_link = ""
        if job_id:
            job_link = f' <a href="/explorer/jobs/{escape(str(job_id))}">job</a>'
        nodes.append(
            f'<div class="chain-node" style="--depth:{int(depth or 0)}">'
            f'<span class="chain-label">{label}</span>'
            f'<span class="muted">{escape(meta)}{job_link}</span>'
            f"</div>"
        )
        if index < len(chain) - 1:
            nodes.append('<div class="chain-arrow" aria-hidden="true">↓</div>')
    return f'<div class="invoke-chain">{"".join(nodes)}</div>'


def link_pills(links: list[dict[str, str]], *, key: str, label_key: str) -> str:
    if not links:
        return '<p class="muted">None yet.</p>'
    pills = []
    for item in links:
        href = item.get("href", "#")
        label = item.get(label_key, item.get(key, "—"))
        pills.append(f'<a class="pill" href="{escape(href)}">{escape(str(label))}</a>')
    return f'<div class="pill-row">{"".join(pills)}</div>'


def schema_form(
    schema: object,
    *,
    action: str,
    method: str = "POST",
    values: dict[str, Any] | None = None,
    errors: list[str] | None = None,
    submit_label: str = "Submit",
    hidden_fields: dict[str, str] | None = None,
) -> str:
    from palm.runtimes.server.surfaces.ssr.explorer import forms

    return forms.schema_form(
        schema,  # type: ignore[arg-type]
        action=action,
        method=method,
        values=values,
        errors=errors,
        submit_label=submit_label,
        hidden_fields=hidden_fields,
    )


def wizard_progress_bar(*, completed: int, total: int, current_step: str | None = None) -> str:
    total = max(total, 1)
    pct = min(100, int((completed / total) * 100))
    step_hint = f" · current: {escape(current_step)}" if current_step else ""
    return (
        '<div class="wizard-progress">'
        '<div class="wizard-progress-track">'
        f'<div class="wizard-progress-fill" style="width:{pct}%"></div>'
        "</div>"
        f'<div class="wizard-progress-label">{completed} of {total} steps{step_hint}</div>'
        "</div>"
    )


def wizard_prompt_card(
    instance_id: str,
    wizard: dict[str, Any],
    *,
    notice: str = "",
    error: str = "",
) -> str:
    from palm.runtimes.server.surfaces.ssr.explorer.forms import alert, wizard_input_form

    status = str(wizard.get("status") or "")
    prompt = wizard.get("prompt") or {}
    banner = ""
    if notice:
        banner += alert(notice)
    if error:
        banner += alert(error, tone="error")

    if status != "WAITING_FOR_INPUT":
        message = "Wizard is not waiting for input."
        if status == "SUCCEEDED":
            message = "Wizard completed successfully."
        elif status in {"FAILED", "CANCELLED"}:
            message = f"Wizard ended with status {status}."
        return (
            f'<section class="wizard-prompt-card" id="wizard-prompt-panel">'
            f"{banner}"
            f'<p class="muted">{escape(message)}</p>'
            f'<p><a href="{_session_api_href(wizard, instance_id)}">REST status</a></p>'
            "</section>"
        )

    if not prompt:
        return (
            f'<section class="wizard-prompt-card" id="wizard-prompt-panel">'
            f"{banner}"
            '<p class="muted">No active prompt — refresh or inspect the job context.</p>'
            "</section>"
        )

    title = prompt.get("title") or prompt.get("step") or "Current step"
    is_collection = _is_collection_prompt(prompt)
    body = (
        collection_form(instance_id, prompt)
        if is_collection
        else wizard_input_form(instance_id, prompt)
    )
    phase_badge = ""
    if is_collection:
        phase = str(prompt.get("collection_phase") or "menu")
        phase_badge = f'<span class="collection-phase-badge">{escape(phase)}</span> '

    return (
        f'<section class="wizard-prompt-card" id="wizard-prompt-panel">'
        f"{banner}"
        f"<h3>{phase_badge}{escape(str(title))}</h3>"
        f"{body}"
        "</section>"
    )


def _is_collection_prompt(prompt: dict[str, Any]) -> bool:
    return prompt.get("step_kind") == "collection" or bool(prompt.get("collection_phase"))


def collection_item_card(
    instance_id: str,
    index: int,
    item: dict[str, Any],
    *,
    label_field: str | None = None,
    item_fields: list[dict[str, Any]] | None = None,
    preview: str | None = None,
    action: str = "menu",
) -> str:
    """Single numbered collection item with edit/remove or select actions."""
    from palm.runtimes.server.surfaces.ssr.explorer.forms import collection_action_form

    title = preview or _collection_item_title(item, index, label_field, item_fields)
    field_lines = _collection_item_field_lines(item, label_field, item_fields)
    fields_html = ""
    if field_lines:
        fields_html = f'<div class="item-fields">{"<br>".join(field_lines)}</div>'

    if action == "select":
        actions_html = collection_action_form(
            instance_id,
            "select_item",
            item_index=index,
            label=f"Select #{index + 1}",
            tone="primary",
        )
    else:
        actions_html = (
            f'<div class="collection-item-actions">'
            f'{collection_action_form(instance_id, "edit", item_index=index, label="Edit", tone="ghost")}'
            f'{collection_action_form(instance_id, "remove", item_index=index, label="Remove", tone="danger")}'
            f"</div>"
        )

    return (
        f'<article class="collection-item-card" role="listitem" data-item-index="{index}">'
        f'<div class="item-number">Item {index + 1}</div>'
        f'<div class="item-title">{escape(title)}</div>'
        f"{fields_html}"
        f"{actions_html}"
        f"</article>"
    )


def collection_list(
    instance_id: str,
    prompt: dict[str, Any],
    *,
    action: str = "menu",
) -> str:
    """Grid of collection item cards."""
    items = prompt.get("collection_items") or []
    if not isinstance(items, list) or not items:
        return '<p class="muted collection-empty">No items yet — add your first one below.</p>'

    previews = prompt.get("collection_item_previews") or []
    label_field = prompt.get("label_field")
    item_fields = prompt.get("item_fields")
    field_specs = list(item_fields) if isinstance(item_fields, list) else None

    cards = []
    for index, raw in enumerate(items):
        if not isinstance(raw, dict):
            continue
        preview = previews[index] if index < len(previews) else None
        cards.append(
            collection_item_card(
                instance_id,
                index,
                raw,
                label_field=label_field,
                item_fields=field_specs,
                preview=str(preview) if preview is not None else None,
                action=action,
            )
        )
    if not cards:
        return '<p class="muted collection-empty">No items yet — add your first one below.</p>'
    return f'<div class="collection-item-grid" role="list">{"".join(cards)}</div>'


def collection_overview_card(instance_id: str, prompt: dict[str, Any]) -> str:
    """Menu-phase collection workspace — item list, progress, and toolbar."""
    from palm.runtimes.server.surfaces.ssr.explorer.forms import collection_action_form

    items = prompt.get("collection_items") or []
    count = len(items) if isinstance(items, list) else 0
    min_items = int(prompt.get("min_items") or 1)
    progress_html = _collection_progress_label(count, min_items)

    prompt_text = prompt.get("text")
    intro = ""
    if prompt_text:
        intro = f'<p class="wizard-prompt-text">{escape(str(prompt_text))}</p>'

    validation = prompt.get("validation_error")
    validation_html = ""
    if validation:
        validation_html = f'<p class="wizard-validation">{escape(str(validation))}</p>'

    done_label = _collection_done_label(prompt, count, min_items)
    can_continue = count >= min_items

    toolbar = (
        f'<div class="collection-toolbar">'
        f'{collection_action_form(instance_id, "add", label="Add New", tone="primary")}'
    )
    if can_continue:
        toolbar += collection_action_form(
            instance_id,
            "done",
            label=done_label,
            tone="primary",
        )
    else:
        toolbar += (
            f'<span class="muted collection-need-more">'
            f"Need {min_items - count} more item{'s' if min_items - count != 1 else ''} to continue"
            f"</span>"
        )
    toolbar += "</div>"

    return (
        f'<div class="collection-overview" role="region" aria-labelledby="collection-overview-title">'
        f'<div class="collection-overview-header">'
        f'<h4 id="collection-overview-title">Collection</h4>'
        f'<div class="collection-count">{progress_html}</div>'
        f"</div>"
        f"{intro}{validation_html}"
        f'{collection_list(instance_id, prompt, action="menu")}'
        f"{toolbar}"
        f"</div>"
    )


def collection_form(instance_id: str, prompt: dict[str, Any]) -> str:
    """Route collection phase to the appropriate panel."""
    from palm.runtimes.server.surfaces.ssr.explorer.forms import (
        collection_field_form,
        collection_remove_form,
        collection_select_form,
    )

    phase = str(prompt.get("collection_phase") or "menu")
    if phase == "field":
        return collection_field_form(instance_id, prompt)
    if phase == "remove_confirm":
        return collection_remove_form(instance_id, prompt)
    if phase == "select_item":
        return collection_select_form(instance_id, prompt)
    return collection_overview_card(instance_id, prompt)


def _collection_progress_label(count: int, min_items: int) -> str:
    if count >= min_items:
        suffix = "ready to continue" if count > min_items else "minimum met"
        return f"<strong>{count}</strong> item{'s' if count != 1 else ''} — {suffix}"
    needed = min_items - count
    return (
        f"<strong>{count}</strong> of <strong>{min_items}</strong> minimum "
        f"({needed} more needed)"
    )


def _collection_done_label(prompt: dict[str, Any], count: int, min_items: int) -> str:
    choices = prompt.get("choices") or []
    if isinstance(choices, list):
        for choice in choices:
            text = str(choice)
            if text.startswith("Continue to summary"):
                return text
    if count < min_items:
        return f"Continue to summary (need {min_items - count} more)"
    return "Continue to summary"


def _collection_item_title(
    item: dict[str, Any],
    index: int,
    label_field: str | None,
    item_fields: list[dict[str, Any]] | None,
) -> str:
    if label_field and item.get(label_field) not in (None, ""):
        return str(item[label_field])
    for field in item_fields or []:
        if not isinstance(field, dict):
            continue
        slug = field.get("slug")
        if slug and item.get(slug) not in (None, ""):
            return str(item[slug])
    for _key, value in item.items():
        if value not in (None, ""):
            return str(value)
    return f"Item {index + 1}"


def _collection_item_field_lines(
    item: dict[str, Any],
    label_field: str | None,
    item_fields: list[dict[str, Any]] | None,
    *,
    max_fields: int = 3,
) -> list[str]:
    lines: list[str] = []
    if item_fields:
        for field in item_fields[:max_fields]:
            if not isinstance(field, dict):
                continue
            slug = field.get("slug")
            if not slug or slug == label_field:
                continue
            value = item.get(slug)
            if value in (None, ""):
                continue
            title = field.get("title") or str(slug).replace("_", " ").title()
            lines.append(f"{escape(title)}: {escape(str(value))}")
        return lines
    for key, value in list(item.items())[:max_fields]:
        if key == label_field or value in (None, ""):
            continue
        lines.append(f"{escape(str(key))}: {escape(str(value))}")
    return lines


def wizard_child_wizards_section(wizard: dict[str, Any], *, instance_id: str = "") -> str:
    """Surface nested child wizards spawned via until_input resource steps."""
    children: list[dict[str, Any]] = []
    prompt = wizard.get("prompt") or {}
    if isinstance(prompt, dict) and prompt.get("waiting_for_child"):
        children.append(
            {
                "step": prompt.get("step") or wizard.get("current_step_slug"),
                "job_id": prompt.get("waiting_for_child_job_id"),
                "instance_id": prompt.get("waiting_for_child_instance_id"),
                "status": prompt.get("child_status"),
                "job_href": prompt.get("child_job_href"),
                "instance_href": prompt.get("child_instance_href"),
                "active": True,
            }
        )

    answers = wizard.get("answers") or {}
    if isinstance(answers, dict):
        for step_key, value in answers.items():
            if not isinstance(value, dict):
                continue
            if not value.get("waiting_for_child_wizard"):
                continue
            children.append(
                {
                    "step": step_key,
                    "job_id": value.get("child_job_id") or value.get("job_id"),
                    "instance_id": value.get("child_instance_id") or value.get("instance_id"),
                    "status": value.get("status"),
                    "job_href": value.get("child_job_href"),
                    "instance_href": value.get("child_instance_href"),
                    "active": False,
                }
            )

    if not children:
        return ""

    rows = []
    for child in children:
        job_id = child.get("job_id")
        instance_id = child.get("instance_id")
        job_link = "—"
        if job_id:
            href = child.get("job_href") or f"/explorer/jobs/{escape(str(job_id))}"
            job_link = f'<a href="{escape(str(href))}">{escape(str(job_id))}</a>'
        instance_link = "—"
        if instance_id:
            href = child.get("instance_href") or f"/explorer/instances/{escape(str(instance_id))}"
            instance_link = f'<a href="{escape(str(href))}">{escape(str(instance_id))}</a>'
        rows.append(
            [
                escape(str(child.get("step") or "—")),
                escape(str(child.get("status") or "WAITING_FOR_INPUT")),
                job_link,
                instance_link,
            ]
        )

    resume_html = ""
    if instance_id and any(child.get("active") for child in children):
        action = f"/explorer/instances/{escape(instance_id)}/resume-child-wait"
        resume_html = (
            '<form action="' + escape(action) + '" method="POST" '
            'hx-post="' + escape(action) + '" '
            'hx-target="#wizard-workspace" hx-swap="outerHTML" '
            'hx-indicator="#wizard-loading" style="margin-top:0.75rem">'
            '<button type="submit" class="btn btn-primary">Check nested wizard / resume parent</button>'
            "</form>"
        )

    return (
        '<section class="panel"><h3>Waiting for nested wizard</h3>'
        '<p class="muted">Parent wizard is suspended until the child flow completes. '
        "Open the child to provide input; the parent resumes automatically when the child succeeds.</p>"
        f'{data_table(["Parent step", "Child status", "Child job", "Child instance"], rows)}'
        f"{resume_html}"
        "</section>"
    )


def wizard_answers_section(wizard: dict[str, Any]) -> str:
    answers = wizard.get("answers") or {}
    if not isinstance(answers, dict) or not answers:
        return (
            '<section class="panel"><h3>Answers so far</h3>'
            '<p class="muted">No answers captured yet.</p></section>'
        )
    rows = [
        [escape(str(key)), escape(_preview_value(value))] for key, value in sorted(answers.items())
    ]
    return (
        '<section class="panel"><h3>Answers so far</h3>'
        f'{data_table(["Step", "Value"], rows)}'
        "</section>"
    )


def wizard_step_timeline(wizard: dict[str, Any], *, instance_id: str) -> str:
    progress = wizard.get("wizard_progress") or {}
    completed = progress.get("completed_steps") or []
    current = progress.get("current_step") or wizard.get("current_step_slug")
    trace = progress.get("backtrack_trace") or []

    if not completed and not current:
        return (
            '<section class="panel"><h3>Step timeline</h3>'
            '<p class="muted">Step history will appear as the wizard advances.</p></section>'
        )

    seen: set[str] = set()
    ordered: list[str] = []
    for slug in completed:
        if isinstance(slug, str) and slug not in seen:
            seen.add(slug)
            ordered.append(slug)
    if isinstance(current, str) and current not in seen:
        ordered.append(current)

    items = []
    for slug in ordered:
        state_class = "active" if slug == current else "done"
        meta = "completed" if slug in completed and slug != current else "current"
        backtrack_btn = ""
        if slug != current and slug in completed:
            backtrack_btn = wizard_backtrack_button(instance_id, slug)
        items.append(
            f'<li class="{state_class}">'
            f'<span class="dot" aria-hidden="true"></span>'
            f'<div><div class="step-label">{escape(slug)}</div>'
            f'<div class="step-meta">{escape(meta)}{backtrack_btn}</div></div>'
            f"</li>"
        )

    trace_items = []
    for entry in trace[-5:]:
        if not isinstance(entry, dict):
            continue
        trace_items.append(
            f'<li><span class="dot"></span><div class="step-meta">'
            f'{escape(str(entry.get("event_type") or "backtrack"))}: '
            f'{escape(str(entry.get("from_step") or "—"))} → '
            f'{escape(str(entry.get("to_step") or "—"))}'
            f"</div></li>"
        )

    trace_html = ""
    if trace_items:
        trace_html = (
            '<h4>Recent backtracks</h4><ul class="wizard-timeline">' f'{"".join(trace_items)}</ul>'
        )

    return (
        '<section class="panel"><h3>Step timeline</h3>'
        f'<ul class="wizard-timeline">{"".join(items)}</ul>'
        f"{trace_html}"
        "</section>"
    )


def wizard_backtrack_button(instance_id: str, to_step: str, *, label: str | None = None) -> str:
    action = f"/explorer/instances/{instance_id}/backtrack"
    text = label or f"Back to {to_step}"
    return (
        f'<form class="wizard-backtrack-inline" action="{escape(action)}" method="POST" '
        f'hx-post="{escape(action)}" hx-target="#wizard-workspace" hx-swap="outerHTML" '
        f'hx-indicator="#wizard-loading" style="display:inline">'
        f'<input type="hidden" name="to_step" value="{escape(to_step)}" />'
        f'<button type="submit" class="wizard-choice-btn" style="margin-left:0.35rem">{escape(text)}</button>'
        f"</form>"
    )


def wizard_backtrack_controls(instance_id: str, wizard: dict[str, Any]) -> str:
    progress = wizard.get("wizard_progress") or {}
    completed = progress.get("completed_steps") or []
    current = progress.get("current_step") or wizard.get("current_step_slug")
    if not completed:
        return ""

    targets = [slug for slug in completed if isinstance(slug, str) and slug != current]
    if not targets:
        return ""

    buttons = [
        (
            f'<form action="/explorer/instances/{escape(instance_id)}/backtrack" method="POST" '
            f'hx-post="/explorer/instances/{escape(instance_id)}/backtrack" '
            f'hx-target="#wizard-workspace" hx-swap="outerHTML" hx-indicator="#wizard-loading">'
            f'<input type="hidden" name="to_step" value="{escape(slug)}" />'
            f'<button type="submit" class="wizard-choice-btn">{escape(f"← {slug}")}</button>'
            f"</form>"
        )
        for slug in reversed(targets[-4:])
    ]
    default_action = f"/explorer/instances/{instance_id}/backtrack"
    return (
        '<section class="panel"><h3>Backtrack</h3>'
        '<p class="muted">Return to a prior step and re-answer. Protected steps cannot be targeted.</p>'
        f'<div class="wizard-choice-grid">{"".join(buttons)}</div>'
        f'<form action="{escape(default_action)}" method="POST" '
        f'hx-post="{escape(default_action)}" hx-target="#wizard-workspace" hx-swap="outerHTML" '
        f'hx-indicator="#wizard-loading" style="margin-top:0.75rem">'
        f'<button type="submit" class="btn btn-default">Back one step</button>'
        f"</form></section>"
    )


def wizard_workspace(
    instance_id: str,
    wizard: dict[str, Any],
    *,
    notice: str = "",
    error: str = "",
    total_steps: int | None = None,
) -> str:
    """Composable wizard detail workspace (full page or HTMX partial)."""
    from palm.runtimes.server.surfaces.ssr.explorer.pages.utils import status_badge

    progress = wizard.get("wizard_progress") or {}
    completed_steps = progress.get("completed_steps") or []
    current = progress.get("current_step") or wizard.get("current_step_slug")
    total = total_steps or max(len(completed_steps) + (1 if current else 0), 1)
    flow_name = (
        wizard.get("flow_name") or wizard.get("wizard_progress", {}).get("wizard_name") or "Wizard"
    )

    header = (
        '<header class="wizard-header">'
        f"<div><h2>{escape(str(flow_name))}</h2>"
        f'<div class="wizard-meta">{badge("wizard", tone="default")} '
        f"{status_badge(str(wizard.get('status') or '—'))}</div></div>"
        f"{wizard_progress_bar(completed=len(completed_steps), total=total, current_step=current)}"
        "</header>"
    )

    prompt_panel = wizard_prompt_card(instance_id, wizard, notice=notice, error=error)
    sidebar = (
        wizard_child_wizards_section(wizard, instance_id=instance_id)
        + wizard_answers_section(wizard)
        + wizard_step_timeline(wizard, instance_id=instance_id)
    )
    backtrack = wizard_backtrack_controls(instance_id, wizard)
    links = (
        '<section class="panel"><h3>Links</h3>'
        f'<p><a href="{_session_api_href(wizard, instance_id)}">REST session API</a> · '
        f'<a href="/explorer/instances/{escape(instance_id)}/snapshots">Snapshots</a>'
    )
    job_id = wizard.get("job_id")
    if job_id:
        links += f' · <a href="/explorer/jobs/{escape(str(job_id))}">Job context</a>'
    links += "</p></section>"

    return (
        f'<div id="wizard-workspace" class="wizard-workspace" aria-live="polite">'
        f"{header}"
        f'<div class="grid-2">{prompt_panel}{sidebar}</div>'
        f"{backtrack}{links}"
        "</div>"
    )


def _preview_value(value: Any) -> str:
    if isinstance(value, dict | list):
        import json

        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)
    return str(value)
