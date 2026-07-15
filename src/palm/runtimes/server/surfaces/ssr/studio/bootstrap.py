"""SSR bootstrap — inject server context into the Studio SPA shell."""

from __future__ import annotations

import json
import re
from typing import TYPE_CHECKING, Any

from palm.runtimes.server.surfaces.ssr.studio.assets import StaticAsset

if TYPE_CHECKING:
    from palm.runtimes.server.context import ServerContext

_BOOTSTRAP_RE = re.compile(
    r'<script id="palm-studio-bootstrap"></script>',
    re.IGNORECASE,
)

_FALLBACK_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Palm Studio</title>
  <style>
    body { font-family: system-ui, sans-serif; background: #0b1220; color: #e8edf7;
           display: grid; place-items: center; min-height: 100vh; margin: 0; }
    main { max-width: 32rem; padding: 2rem; text-align: center; }
    h1 { font-size: 1.5rem; margin-bottom: 0.5rem; }
    p { color: #9aa8c7; line-height: 1.5; }
    code { background: #151d2e; padding: 0.15rem 0.4rem; border-radius: 0.25rem; }
  </style>
</head>
<body>
  <main>
    <h1>Palm Studio</h1>
    <p>Frontend assets are not built yet. Run
      <code>npm install &amp;&amp; npm run build</code> in
      <code>src/palm/runtimes/server/surfaces/ssr/studio/frontend</code>.
    </p>
  </main>
  <script id="palm-studio-bootstrap"></script>
</body>
</html>
"""


def bootstrap_payload(ctx: ServerContext) -> dict[str, Any]:
    """Serializable config injected into the SPA at load time."""
    return {
        "version": ctx.runtime.version,
        "runtime": ctx.runtime.runtime_name,
        "apiBase": "/v1",
        "explorer": "/explorer",
        "studio": "/studio",
    }


def render_shell(ctx: ServerContext, asset: StaticAsset | None) -> str:
    """Return HTML with an inline bootstrap script for the Studio client."""
    html = asset.path.read_text(encoding="utf-8") if asset is not None else _FALLBACK_HTML
    payload = json.dumps(bootstrap_payload(ctx), separators=(",", ":"))
    script = f'<script id="palm-studio-bootstrap">window.__PALM_STUDIO__={payload};</script>'
    if _BOOTSTRAP_RE.search(html):
        return _BOOTSTRAP_RE.sub(script, html, count=1)
    return html.replace("</head>", f"  {script}\n</head>", 1)
