"""Self-contained HTML API documentation (zero external dependencies)."""

from __future__ import annotations

import html
import json

from palm.runtimes.server.surfaces.rest.doc_examples import (
    GROUP_DESCRIPTIONS,
    QUERY_HINTS,
    REQUEST_BODIES,
    build_curl,
    response_example,
    schema_fields,
)
from palm.runtimes.server.surfaces.rest.route_table import RouteDefinition, rest_routes

_METHOD_COLORS = {
    "GET": "#14b8a6",
    "POST": "#3b82f6",
    "PUT": "#f59e0b",
    "DELETE": "#ef4444",
    "PATCH": "#a855f7",
}


def build_docs_html(*, version: str) -> str:
    """Render a rich HTML documentation hub for the REST surface."""
    groups: dict[str, list[RouteDefinition]] = {}
    for route in rest_routes():
        groups.setdefault(route.group, []).append(route)

    nav_items = []
    sections = []
    for group, routes in groups.items():
        anchor = _group_anchor(group)
        nav_items.append(
            f'<a class="nav-link" href="#{anchor}">{html.escape(group)}</a>'
        )
        cards = "\n".join(_endpoint_card(route) for route in routes)
        description = GROUP_DESCRIPTIONS.get(group, "")
        sections.append(
            f'<section class="group" id="{anchor}">'
            f"<h2>{html.escape(group)}</h2>"
            f'<p class="group-desc">{html.escape(description)}</p>'
            f"{cards}"
            f"</section>"
        )

    nav = "\n".join(nav_items)
    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Palm Engine API v{html.escape(version)}</title>
  <style>
    :root {{
      --bg: #09090b;
      --surface: #18181b;
      --border: #3f3f46;
      --text: #fafafa;
      --muted: #a1a1aa;
      --accent: #14b8a6;
      --accent-dim: #0d9488;
      --code-bg: #0c0c0e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      font-family: system-ui, -apple-system, sans-serif;
      margin: 0;
      background: var(--bg);
      color: var(--text);
      line-height: 1.55;
    }}
    a {{ color: var(--accent); text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .layout {{
      display: grid;
      grid-template-columns: 220px 1fr;
      min-height: 100vh;
    }}
    .sidebar {{
      position: sticky;
      top: 0;
      height: 100vh;
      overflow-y: auto;
      padding: 1.5rem 1rem;
      border-right: 1px solid var(--border);
      background: var(--surface);
    }}
    .sidebar h1 {{
      font-size: 1.1rem;
      margin: 0 0 0.25rem;
    }}
    .sidebar .version {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 1rem; }}
    .nav-link {{
      display: block;
      padding: 0.35rem 0.5rem;
      border-radius: 0.375rem;
      color: var(--muted);
      font-size: 0.9rem;
    }}
    .nav-link:hover {{ background: var(--bg); color: var(--text); text-decoration: none; }}
    .sidebar-links {{ margin-top: 1.25rem; padding-top: 1rem; border-top: 1px solid var(--border); }}
    .sidebar-links a {{ display: block; font-size: 0.85rem; margin-bottom: 0.4rem; }}
    main {{ padding: 2rem 2.5rem 4rem; max-width: 960px; }}
    .hero {{ margin-bottom: 2rem; }}
    .hero p {{ color: var(--muted); max-width: 42rem; }}
    .pill-row {{ display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem; }}
    .pill {{
      font-size: 0.8rem;
      padding: 0.25rem 0.65rem;
      border-radius: 999px;
      border: 1px solid var(--border);
      color: var(--muted);
    }}
    .group {{ margin-bottom: 2.5rem; }}
    .group h2 {{ font-size: 1.5rem; margin-bottom: 0.25rem; }}
    .group-desc {{ color: var(--muted); margin: 0 0 1rem; }}
    .endpoint-card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 0.75rem;
      padding: 1.25rem;
      margin-bottom: 1rem;
    }}
    .endpoint-header {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 0.6rem;
      margin-bottom: 0.5rem;
    }}
    .method {{
      font-size: 0.75rem;
      font-weight: 700;
      letter-spacing: 0.04em;
      padding: 0.2rem 0.5rem;
      border-radius: 0.25rem;
      color: #fff;
    }}
    .path {{ font-family: ui-monospace, monospace; font-size: 0.95rem; }}
    .badge {{
      font-size: 0.7rem;
      padding: 0.15rem 0.45rem;
      border-radius: 0.25rem;
      border: 1px solid var(--border);
      color: var(--muted);
    }}
    .badge.auth {{ border-color: #f59e0b55; color: #fbbf24; }}
    .summary {{ font-weight: 600; margin: 0.25rem 0; }}
    .description {{ color: var(--muted); font-size: 0.92rem; margin: 0 0 0.75rem; }}
    .schema-row {{ display: flex; flex-wrap: wrap; gap: 0.4rem; margin-bottom: 0.75rem; }}
    .schema-tag {{
      font-size: 0.75rem;
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 0.25rem;
      padding: 0.15rem 0.45rem;
      color: var(--accent);
    }}
    .example {{ margin-top: 0.75rem; }}
    .example-label {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.8rem;
      color: var(--muted);
      margin-bottom: 0.35rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}
    .copy-btn {{
      background: transparent;
      border: 1px solid var(--border);
      color: var(--muted);
      font-size: 0.75rem;
      padding: 0.15rem 0.5rem;
      border-radius: 0.25rem;
      cursor: pointer;
    }}
    .copy-btn:hover {{ border-color: var(--accent); color: var(--accent); }}
    pre {{
      margin: 0;
      padding: 0.85rem 1rem;
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 0.5rem;
      overflow-x: auto;
      font-size: 0.82rem;
      line-height: 1.45;
    }}
    code {{ font-family: ui-monospace, monospace; color: #e4e4e7; }}
    @media (max-width: 768px) {{
      .layout {{ grid-template-columns: 1fr; }}
      .sidebar {{ position: static; height: auto; border-right: none; border-bottom: 1px solid var(--border); }}
      main {{ padding: 1.25rem; }}
    }}
  </style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <h1>Palm Engine API</h1>
      <div class="version">v{html.escape(version)}</div>
      <nav>{nav}</nav>
      <div class="sidebar-links">
        <a href="/wiki">Palm Wiki (SSR)</a>
        <a href="/v1/openapi.json">OpenAPI JSON</a>
        <a href="/health">Health check</a>
        <a href="https://github.com/JGabrielGruber/palmengine">GitHub</a>
      </div>
    </aside>
    <main>
      <div class="hero">
        <h2>REST API Reference</h2>
        <p>Registry-driven orchestration surface. Submit flows, stage plans, inspect jobs
           and instances, browse the definition catalog, and inspect state snapshots.
           All list endpoints return a resource key plus a <code>pagination</code> block.</p>
        <div class="pill-row">
          <span class="pill">Base URL: <code>http://host:port</code></span>
          <span class="pill">Auth header: <code>X-Palm-Subject</code> (when enforced)</span>
          <span class="pill">Errors: <code>{{"error", "message", "details?"}}</code></span>
        </div>
      </div>
      {body}
    </main>
  </div>
  <script>
    function copyExample(btn) {{
      const code = btn.closest('.example').querySelector('code');
      navigator.clipboard.writeText(code.textContent).then(() => {{
        const original = btn.textContent;
        btn.textContent = 'Copied!';
        setTimeout(() => {{ btn.textContent = original; }}, 1500);
      }});
    }}
  </script>
</body>
</html>"""


def _group_anchor(group: str) -> str:
    return group.lower().replace(" ", "-")


def _endpoint_card(route: RouteDefinition) -> str:
    method_color = _METHOD_COLORS.get(route.method, "#71717a")
    auth_badge = (
        '<span class="badge auth">auth required</span>' if route.auth_required else ""
    )
    status_badge = (
        f'<span class="badge">{route.response_status}</span>'
        if route.response_status != 200
        else ""
    )

    schema_tags = _schema_tags(route)
    curl = html.escape(build_curl(route))
    response = response_example(route)
    response_block = ""
    if response:
        response_block = (
            '<div class="example">'
            '<div class="example-label"><span>Sample response</span></div>'
            f"<pre><code>{html.escape(response)}</code></pre>"
            "</div>"
        )

    request_block = ""
    if route.request_schema:
        body = html.escape(
            json.dumps(REQUEST_BODIES.get(route.request_schema, {}), indent=2)
        )
        request_block = (
            '<div class="example">'
            '<div class="example-label"><span>Request body</span></div>'
            f"<pre><code>{body}</code></pre>"
            "</div>"
        )

    return (
        f'<article class="endpoint-card" id="{html.escape(route.route_id)}">'
        f'<div class="endpoint-header">'
        f'<span class="method" style="background:{method_color}">{html.escape(route.method)}</span>'
        f'<code class="path">{html.escape(route.path)}</code>'
        f"{auth_badge}{status_badge}"
        f"</div>"
        f'<p class="summary">{html.escape(route.summary)}</p>'
        f'<p class="description">{html.escape(route.description)}</p>'
        f"{schema_tags}"
        f'<div class="example">'
        f'<div class="example-label"><span>Try it</span>'
        f'<button class="copy-btn" type="button" onclick="copyExample(this)">Copy</button></div>'
        f"<pre><code>{curl}</code></pre>"
        f"</div>"
        f"{request_block}"
        f"{response_block}"
        f"</article>"
    )


def _schema_tags(route: RouteDefinition) -> str:
    tags: list[str] = []
    if route.request_schema:
        for field in schema_fields(route.request_schema):
            tags.append(f'<span class="schema-tag">{html.escape(field)}</span>')
    if route.query_schema:
        hint = QUERY_HINTS.get(route.query_schema, route.query_schema)
        tags.append(f'<span class="schema-tag">query: {html.escape(hint)}</span>')
    if not tags:
        return ""
    return f'<div class="schema-row">{"".join(tags)}</div>'