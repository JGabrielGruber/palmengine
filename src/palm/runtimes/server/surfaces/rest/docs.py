"""Self-contained HTML API documentation (zero external dependencies)."""

from __future__ import annotations

import html

from palm.runtimes.server.surfaces.rest.route_table import rest_routes


def build_docs_html(*, version: str) -> str:
    """Render a lightweight HTML overview of the REST surface."""
    groups: dict[str, list[str]] = {}
    for route in rest_routes():
        entry = (
            f"<tr><td><code>{html.escape(route.method)}</code></td>"
            f"<td><code>{html.escape(route.path)}</code></td>"
            f"<td>{html.escape(route.summary)}</td>"
            f"<td>{html.escape(route.description)}</td></tr>"
        )
        groups.setdefault(route.group, []).append(entry)

    sections = []
    for group, rows in groups.items():
        table = (
            "<table><thead><tr><th>Method</th><th>Path</th>"
            "<th>Summary</th><th>Description</th></tr></thead><tbody>"
            + "".join(rows)
            + "</tbody></table>"
        )
        sections.append(f"<section><h2>{html.escape(group)}</h2>{table}</section>")

    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Palm Engine API v{html.escape(version)}</title>
  <style>
    body {{ font-family: system-ui, sans-serif; margin: 2rem; line-height: 1.5; }}
    h1 {{ margin-bottom: 0.25rem; }}
    .meta {{ color: #555; margin-bottom: 1.5rem; }}
    table {{ border-collapse: collapse; width: 100%; margin-bottom: 1.5rem; }}
    th, td {{ border: 1px solid #ddd; padding: 0.5rem 0.75rem; text-align: left; vertical-align: top; }}
    th {{ background: #f6f6f6; }}
    code {{ font-size: 0.9em; }}
    a {{ color: #0b5; }}
  </style>
</head>
<body>
  <h1>Palm Engine API</h1>
  <p class="meta">Version {html.escape(version)} ·
    <a href="/v1/openapi.json">OpenAPI JSON</a> ·
    <a href="/health">Health</a>
  </p>
  <p>Registry-driven REST surface for Palm orchestration. Submit flows, stage plans,
     inspect jobs and instances, and provide interactive wizard input.</p>
  {body}
</body>
</html>"""