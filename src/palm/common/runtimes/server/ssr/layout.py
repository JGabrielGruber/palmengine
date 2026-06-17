"""SSR layout helpers — shared page shell for surface-specific UIs."""

from __future__ import annotations

from collections.abc import Sequence

from palm.common.runtimes.server.ssr.render import escape

PALM_SSR_CSS = """
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
main { padding: 2rem 2.5rem 4rem; max-width: 80rem; }
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
.schema-form { max-width: 36rem; }
.form-field { margin-bottom: 1rem; }
.form-field label {
  display: block; font-size: 0.85rem; color: var(--muted); margin-bottom: 0.35rem;
}
.form-field input, .form-field select, .form-field textarea {
  width: 100%; padding: 0.55rem 0.65rem; border-radius: 0.45rem;
  border: 1px solid var(--border); background: var(--bg); color: var(--text);
  font: inherit;
}
.form-field textarea { font-family: ui-monospace, monospace; font-size: 0.85rem; }
.field-hint { display: block; font-size: 0.78rem; color: var(--muted); margin-top: 0.25rem; }
.form-errors { margin: 0; padding-left: 1.1rem; }
.form-actions { margin-top: 1.25rem; }
.btn-primary {
  background: var(--accent-soft); color: var(--text); border: none;
  padding: 0.55rem 1.1rem; border-radius: 0.45rem; font-weight: 600; cursor: pointer;
}
.btn-primary:hover { background: var(--accent); }
.alert { padding: 0.75rem 1rem; border-radius: 0.5rem; margin-bottom: 1rem; }
.alert-success { background: #042f2e; border: 1px solid var(--accent); color: var(--text); }
.alert-error { background: #450a0a; border: 1px solid var(--rose); color: var(--text); }
.btn {
  display: inline-block; font-size: 0.85rem; font-weight: 600;
  padding: 0.4rem 0.75rem; border-radius: 0.4rem; text-decoration: none;
}
.btn-primary { background: var(--accent-soft); color: var(--text); border: 1px solid var(--accent); }
.btn-primary:hover { background: var(--accent); text-decoration: none; }
.btn-row { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
.form-section { margin: 1.25rem 0; padding-top: 0.5rem; border-top: 1px solid var(--border); }
.form-section h4 { margin: 0 0 0.75rem; font-size: 0.95rem; }
.flow-context-panel { margin-top: 0.75rem; padding: 0.85rem 1rem; }
.muted-section { opacity: 0.92; }
.flow-submit-stack { display: flex; flex-direction: column; gap: 1.25rem; }
.advanced-panel {
  border: 1px solid var(--border); border-radius: 0.6rem; padding: 0.85rem 1rem;
  background: var(--surface);
}
.advanced-panel summary { cursor: pointer; font-weight: 600; color: var(--muted); }
.advanced-panel[open] summary { margin-bottom: 0.75rem; color: var(--text); }
@media (max-width: 768px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { position: static; height: auto; border-right: none; border-bottom: 1px solid var(--border); }
  main { padding: 1.25rem; }
}
"""


def page_shell(
    *,
    title: str,
    brand: str,
    version: str,
    content: str,
    nav: Sequence[tuple[str, str]],
    active_nav: str,
    subtitle: str = "",
    footer_pills: Sequence[tuple[str, str]] = (),
    extra_css: str = "",
) -> str:
    """Wrap content in a sidebar layout shell for SSR surfaces."""
    nav_html = []
    for label, href in nav:
        active = " active" if href == active_nav else ""
        nav_html.append(f'<a class="nav-link{active}" href="{escape(href)}">{escape(label)}</a>')

    pills = []
    for label, href in footer_pills:
        pills.append(f'<span class="pill"><a href="{escape(href)}">{escape(label)}</a></span>')

    subtitle_html = f"<p>{escape(subtitle)}</p>" if subtitle else ""
    css = PALM_SSR_CSS + extra_css
    pills_html = f'<div class="pill-row" style="margin-top:1.5rem">{"".join(pills)}</div>' if pills else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(title)} · {escape(brand)}</title>
  <style>{css}</style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">{escape(brand)}</div>
      <div class="version">v{escape(version)}</div>
      <nav>{"".join(nav_html)}</nav>
      {pills_html}
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