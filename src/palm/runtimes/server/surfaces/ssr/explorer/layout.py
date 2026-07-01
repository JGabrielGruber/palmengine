"""Palm Explorer layout — branded shell over shared SSR helpers."""

from __future__ import annotations

from palm.common.runtimes.server.ssr.layout import page_shell

_EXPLORER_NAV = (
    ("Home", "/explorer"),
    ("Assist", "/explorer/assist"),
    ("Flows", "/explorer/flows"),
    ("Processes", "/explorer/processes"),
    ("Resources", "/explorer/resources"),
    ("Patterns", "/explorer/patterns"),
    ("Schemas", "/explorer/schemas"),
    ("Jobs", "/explorer/jobs"),
    ("Instances", "/explorer/instances"),
    ("API Reference", "/v1/docs"),
    ("Examples", "/explorer/examples"),
)

_FOOTER_PILLS = (("Health", "/health"), ("OpenAPI", "/v1/openapi.json"))


_HTMX_SCRIPT = (
    '<script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.min.js"'
    'integrity="sha384-H5SrcfygHmAuTDZphMHqBJLc3FhssKjG7w/CeCpFReSfwBWDTKpkzPP8c+cLsK+V"'
    'crossorigin="anonymous"></script>'
)

_WIZARD_EXPLORER_CSS = """
.wizard-workspace { display: flex; flex-direction: column; gap: 1.25rem; }
.wizard-header {
  display: flex; flex-wrap: wrap; gap: 1rem; align-items: center; justify-content: space-between;
  padding: 1.25rem; border-radius: 0.85rem; border: 1px solid var(--border);
  background: linear-gradient(135deg, #0c1f1d 0%, var(--surface) 55%);
}
.wizard-header h2 { margin: 0; font-size: 1.35rem; }
.wizard-meta { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
.wizard-progress { flex: 1 1 12rem; min-width: 10rem; }
.wizard-progress-track {
  height: 0.45rem; border-radius: 999px; background: var(--surface-2); overflow: hidden;
}
.wizard-progress-fill {
  height: 100%; background: linear-gradient(90deg, var(--accent-soft), var(--accent));
  border-radius: 999px; transition: width 0.35s ease;
}
.wizard-progress-label { font-size: 0.8rem; color: var(--muted); margin-top: 0.35rem; }
.wizard-prompt-card {
  border: 1px solid var(--accent); border-radius: 0.85rem; padding: 1.35rem;
  background: #0a1615; box-shadow: 0 0 0 1px rgba(20, 184, 166, 0.08);
}
.wizard-prompt-card h3 { margin: 0 0 0.35rem; font-size: 1.15rem; }
.wizard-prompt-text { font-size: 1.05rem; margin: 0 0 1rem; color: var(--text); }
.wizard-choice-grid {
  display: flex; flex-wrap: wrap; gap: 0.5rem; margin-bottom: 1rem;
}
.wizard-choice-btn {
  background: var(--surface-2); color: var(--text); border: 1px solid var(--border);
  padding: 0.5rem 0.9rem; border-radius: 0.5rem; cursor: pointer; font: inherit;
}
.wizard-choice-btn:hover, .wizard-choice-btn:focus {
  border-color: var(--accent); background: #0d3d38; outline: none;
}
.wizard-choice-btn[aria-pressed="true"] {
  border-color: var(--accent); background: var(--accent-soft);
}
.wizard-validation { color: var(--rose); font-size: 0.88rem; margin-bottom: 0.75rem; }
.wizard-timeline { list-style: none; padding: 0; margin: 0; }
.wizard-timeline li {
  display: flex; gap: 0.65rem; align-items: flex-start; padding: 0.55rem 0;
  border-bottom: 1px solid var(--border);
}
.wizard-timeline .dot {
  width: 0.55rem; height: 0.55rem; border-radius: 999px; margin-top: 0.45rem;
  background: var(--border); flex-shrink: 0;
}
.wizard-timeline li.active .dot { background: var(--accent); box-shadow: 0 0 0 3px rgba(20,184,166,0.25); }
.wizard-timeline li.done .dot { background: var(--accent-soft); }
.wizard-timeline .step-label { font-weight: 600; }
.wizard-timeline .step-meta { color: var(--muted); font-size: 0.82rem; }
.wizard-answers-table td:first-child { color: var(--muted); width: 8rem; }
.collection-items { list-style: none; padding: 0; margin: 0 0 1rem; }
.collection-items li {
  padding: 0.45rem 0.65rem; border: 1px solid var(--border); border-radius: 0.45rem;
  margin-bottom: 0.35rem; background: var(--surface-2);
}
.htmx-indicator { opacity: 0; transition: opacity 0.2s; }
.htmx-request .htmx-indicator { opacity: 1; }
.wizard-loading { color: var(--muted); font-size: 0.85rem; }
.collection-overview {
  border: 1px solid var(--border); border-radius: 0.85rem; padding: 1.1rem;
  background: var(--surface); margin-bottom: 1rem;
}
.collection-overview-header {
  display: flex; flex-wrap: wrap; gap: 0.75rem; align-items: center;
  justify-content: space-between; margin-bottom: 0.85rem;
}
.collection-count { font-size: 0.88rem; color: var(--muted); }
.collection-count strong { color: var(--accent); }
.collection-item-grid {
  display: grid; gap: 0.65rem; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  margin-bottom: 1rem;
}
.collection-item-card {
  border: 1px solid var(--border); border-radius: 0.65rem; padding: 0.85rem;
  background: var(--surface-2); position: relative;
}
.collection-item-card .item-number {
  font-size: 0.72rem; font-weight: 700; color: var(--accent); letter-spacing: 0.06em;
  text-transform: uppercase; margin-bottom: 0.25rem;
}
.collection-item-card .item-title { font-weight: 600; margin-bottom: 0.35rem; }
.collection-item-card .item-fields { font-size: 0.82rem; color: var(--muted); }
.collection-item-actions {
  display: flex; flex-wrap: wrap; gap: 0.35rem; margin-top: 0.65rem;
}
.collection-toolbar {
  display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center;
  padding-top: 0.5rem; border-top: 1px solid var(--border);
}
.collection-phase-badge {
  font-size: 0.72rem; font-weight: 700; letter-spacing: 0.05em;
  text-transform: uppercase; color: var(--amber);
}
.collection-draft-panel {
  margin: 0.75rem 0; padding: 0.75rem; border-radius: 0.5rem;
  border: 1px dashed var(--border); background: #0c1211;
}
.collection-remove-confirm {
  border: 1px solid var(--rose); border-radius: 0.75rem; padding: 1.1rem;
  background: #1a0a0d;
}
.collection-remove-preview {
  margin: 0.75rem 0; padding: 0.75rem; border-radius: 0.5rem;
  background: var(--surface-2); border: 1px solid var(--border);
}
.collection-field-progress {
  font-size: 0.82rem; color: var(--muted); margin-bottom: 0.75rem;
}
.btn-danger {
  background: #7f1d1d; color: var(--text); border: 1px solid var(--rose);
}
.btn-danger:hover { background: #991b1b; }
.btn-ghost {
  background: transparent; color: var(--muted); border: 1px solid var(--border);
}
.btn-ghost:hover { color: var(--text); border-color: var(--accent); }
.collection-action-form { display: inline-block; }
.wizard-choice-btn:focus-visible,
.btn-primary:focus-visible,
.btn-ghost:focus-visible,
.btn-danger:focus-visible {
  outline: 2px solid var(--accent); outline-offset: 2px;
}
@media (max-width: 640px) {
  .collection-item-grid { grid-template-columns: 1fr; }
  .wizard-header { flex-direction: column; align-items: stretch; }
  .collection-toolbar { flex-direction: column; align-items: stretch; }
  .collection-toolbar .collection-action-form { width: 100%; }
  .collection-toolbar .collection-action-form button { width: 100%; }
}
@media (prefers-reduced-motion: reduce) {
  .wizard-progress-fill, .htmx-indicator { transition: none; }
}
"""


def explorer_page(
    *,
    title: str,
    version: str,
    content: str,
    active_nav: str = "/explorer",
    subtitle: str = "",
    extra_css: str = "",
    enable_htmx: bool = True,
) -> str:
    """Wrap page content in the Palm Explorer layout."""
    head = _HTMX_SCRIPT if enable_htmx else ""
    return page_shell(
        title=title,
        brand="Palm Explorer",
        version=version,
        content=content,
        nav=_EXPLORER_NAV,
        active_nav=active_nav,
        subtitle=subtitle,
        footer_pills=_FOOTER_PILLS,
        extra_css=_WIZARD_EXPLORER_CSS + extra_css,
        extra_head=head,
    )


def wiki_page(
    *,
    title: str,
    version: str,
    content: str,
    active_nav: str = "/explorer",
    subtitle: str = "",
) -> str:
    """Backward-compatible alias for :func:`explorer_page`."""
    return explorer_page(
        title=title,
        version=version,
        content=content,
        active_nav=active_nav,
        subtitle=subtitle,
    )
