"""SSR HTML components — small composable fragments."""

from __future__ import annotations

from typing import Any

from palm.common.runtimes.server.ssr.render import escape, pretty_json


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
            f'<p><a href="/v1/wizards/{escape(instance_id)}">REST status</a></p>'
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
    return (
        f'<section class="wizard-prompt-card" id="wizard-prompt-panel">'
        f"{banner}"
        f"<h3>{escape(str(title))}</h3>"
        f"{wizard_input_form(instance_id, prompt)}"
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
        [escape(str(key)), escape(_preview_value(value))]
        for key, value in sorted(answers.items())
    ]
    return (
        '<section class="panel"><h3>Answers so far</h3>'
        f'{data_table(["Step", "Value"], rows)}'
        "</section>"
    )


def wizard_step_timeline(wizard: dict[str, Any], *, instance_id: str) -> str:
    progress = wizard.get("wizard_progress") or {}
    completed = progress.get("completed_steps") or []
    current = progress.get("current_step") or wizard.get("wizard_step_slug")
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
            '<h4>Recent backtracks</h4><ul class="wizard-timeline">'
            f'{"".join(trace_items)}</ul>'
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
    current = progress.get("current_step") or wizard.get("wizard_step_slug")
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
    current = progress.get("current_step") or wizard.get("wizard_step_slug")
    total = total_steps or max(len(completed_steps) + (1 if current else 0), 1)
    flow_name = wizard.get("flow_name") or wizard.get("wizard_progress", {}).get("wizard_name") or "Wizard"

    header = (
        '<header class="wizard-header">'
        f"<div><h2>{escape(str(flow_name))}</h2>"
        f'<div class="wizard-meta">{badge("wizard", tone="default")} '
        f"{status_badge(str(wizard.get('status') or '—'))}</div></div>"
        f"{wizard_progress_bar(completed=len(completed_steps), total=total, current_step=current)}"
        "</header>"
    )

    prompt_panel = wizard_prompt_card(instance_id, wizard, notice=notice, error=error)
    sidebar = wizard_answers_section(wizard) + wizard_step_timeline(wizard, instance_id=instance_id)
    backtrack = wizard_backtrack_controls(instance_id, wizard)
    links = (
        '<section class="panel"><h3>Links</h3>'
        f'<p><a href="/v1/wizards/{escape(instance_id)}">REST wizard API</a> · '
        f'<a href="/explorer/instances/{escape(instance_id)}/snapshots">Snapshots</a>'
    )
    job_id = wizard.get("job_id")
    if job_id:
        links += f' · <a href="/explorer/jobs/{escape(str(job_id))}">Job context</a>'
    links += "</p></section>"

    return (
        f'<div id="wizard-workspace" class="wizard-workspace">'
        f"{header}"
        f'<div class="grid-2">{prompt_panel}{sidebar}</div>'
        f"{backtrack}{links}"
        "</div>"
    )


def _preview_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        import json

        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)
    return str(value)
