"""SSR page layout — Palm-themed wiki shell."""

from __future__ import annotations

from palm.common.runtimes.server.ssr.render import escape

_WIKI_NAV = (
    ("Overview", "/wiki"),
    ("Flows", "/wiki/flows"),
    ("Processes", "/wiki/processes"),
    ("Patterns", "/wiki/patterns"),
    ("Schemas", "/wiki/schemas"),
    ("Jobs", "/wiki/jobs"),
    ("API Reference", "/v1/docs"),
    ("Examples", "/wiki/examples"),
)

_PALM_CSS = """
:root {
  --bg: #09090b;
  --surface: #18181b;
  --surface-2: #27272a;
  --border: #3f3f46;
  --text: #fafafa;
  --muted: #a1a1aa;
  --accent: #14b8a6;
  --accent-soft: #0d9488;
  --rose: #fb7185;
  --amber: #fbbf24;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: system-ui, -apple-system, sans-serif;
  background: var(--bg);
  color: var(--text);
  line-height: 1.55;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.layout { display: grid; grid-template-columns: 240px 1fr; min-height: 100vh; }
.sidebar {
  position: sticky; top: 0; height: 100vh; overflow-y: auto;
  padding: 1.5rem 1rem; border-right: 1px solid var(--border);
  background: var(--surface);
}
.brand { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.25rem; }
.version { color: var(--muted); font-size: 0.85rem; margin-bottom: 1.25rem; }
.nav-link {
  display: block; padding: 0.4rem 0.55rem; border-radius: 0.4rem;
  color: var(--muted); font-size: 0.92rem; margin-bottom: 0.15rem;
}
.nav-link:hover, .nav-link.active {
  background: var(--bg); color: var(--text); text-decoration: none;
}
main { padding: 2rem 2.5rem 4rem; max-width: 1100px; }
.hero { margin-bottom: 2rem; }
.hero h1 { font-size: 2rem; margin: 0 0 0.5rem; }
.hero p { color: var(--muted); max-width: 46rem; margin: 0; }
.section { margin-bottom: 2rem; }
.section h2 { font-size: 1.35rem; margin: 0 0 0.75rem; }
.grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; }
.grid-2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
.stat-card {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 0.75rem; padding: 1rem;
}
.stat-value { font-size: 1.75rem; font-weight: 700; color: var(--accent); }
.stat-label { color: var(--muted); font-size: 0.9rem; }
.stat-hint { color: var(--muted); font-size: 0.8rem; margin-top: 0.25rem; }
.link-card {
  display: block; background: var(--surface); border: 1px solid var(--border);
  border-radius: 0.75rem; padding: 1rem; color: inherit;
}
.link-card:hover { border-color: var(--accent); text-decoration: none; }
.link-card h3 { margin: 0 0 0.35rem; font-size: 1rem; }
.link-card p { margin: 0; color: var(--muted); font-size: 0.9rem; }
.data-table {
  width: 100%; border-collapse: collapse; background: var(--surface);
  border: 1px solid var(--border); border-radius: 0.75rem; overflow: hidden;
}
.data-table th, .data-table td {
  border-bottom: 1px solid var(--border); padding: 0.65rem 0.85rem; text-align: left;
}
.data-table th { background: var(--surface-2); color: var(--muted); font-size: 0.8rem; }
.code-block {
  background: #0c0c0e; border: 1px solid var(--border); border-radius: 0.6rem;
  padding: 1rem; overflow-x: auto; font-size: 0.82rem; line-height: 1.45;
}
.muted { color: var(--muted); }
.panel {
  background: var(--surface); border: 1px solid var(--border);
  border-radius: 0.75rem; padding: 1.25rem; margin-bottom: 1rem;
}
.panel h3 { margin: 0 0 0.75rem; font-size: 1rem; }
.badge {
  display: inline-block; font-size: 0.72rem; font-weight: 700;
  letter-spacing: 0.04em; padding: 0.15rem 0.45rem; border-radius: 0.25rem;
}
.badge-default { background: var(--surface-2); color: var(--muted); }
.badge-waiting { background: #422006; color: var(--amber); }
.badge-success { background: #042f2e; color: var(--accent); }
.badge-error { background: #450a0a; color: var(--rose); }
.action-list, .event-timeline { list-style: none; padding: 0; margin: 0; }
.action-item, .event-item { padding: 0.45rem 0; border-bottom: 1px solid var(--border); }
.action-item .method, .event-item .event-type {
  font-size: 0.75rem; font-weight: 700; color: var(--accent);
}
.event-item time { color: var(--muted); font-size: 0.82rem; margin-right: 0.5rem; }
.pill-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem; }
.pill {
  font-size: 0.8rem; padding: 0.25rem 0.65rem; border-radius: 999px;
  border: 1px solid var(--border); color: var(--muted);
}
@media (max-width: 768px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { position: static; height: auto; border-right: none; border-bottom: 1px solid var(--border); }
  main { padding: 1.25rem; }
}
"""


def wiki_page(
    *,
    title: str,
    version: str,
    content: str,
    active_nav: str = "/wiki",
    subtitle: str = "",
) -> str:
    """Wrap page content in the wiki layout."""
    nav = []
    for label, href in _WIKI_NAV:
        active = " active" if href == active_nav else ""
        nav.append(f'<a class="nav-link{active}" href="{escape(href)}">{escape(label)}</a>')
    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(title)} · Palm Wiki</title>
  <style>{_PALM_CSS}</style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">Palm Wiki</div>
      <div class="version">v{escape(version)}</div>
      <nav>{"".join(nav)}</nav>
      <div class="pill-row" style="margin-top:1.5rem">
        <span class="pill"><a href="/health">Health</a></span>
        <span class="pill"><a href="/v1/openapi.json">OpenAPI</a></span>
      </div>
    </aside>
    <main>
      <div class="hero">
        <h1>{escape(title)}</h1>
        {subtitle_html}
      </div>
      {content}
    </main>
  </div>
</body>
</html>"""