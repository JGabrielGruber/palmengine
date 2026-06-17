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


def alert(message: str, *, tone: str = "success") -> str:
    from palm.common.runtimes.server.ssr.forms import alert as _alert

    return _alert(message, tone=tone)


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
    from palm.common.runtimes.server.ssr.forms import schema_form as _schema_form

    return _schema_form(
        schema,  # type: ignore[arg-type]
        action=action,
        method=method,
        values=values,
        errors=errors,
        submit_label=submit_label,
        hidden_fields=hidden_fields,
    )