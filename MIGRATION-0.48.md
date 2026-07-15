# MIGRATION — 0.48 (T2, ApplicationHost decomposition)

0.48 decomposes `ApplicationHost` into modular collaborators (internal, no API change)
and relocates one misplaced composition root. Only the latter is import-visible.

## `ServerContext` / `ServerApp` moved out of `common` (0.48.7, PD-013)

The server **composition roots** — which instantiate the service layer — moved from
`palm.common.runtimes.server` (shared *infrastructure*) to `palm.runtimes.server` (the
network runtime), where a composition root belongs. Reusable server infra
(`ServerRequest`/`ServerResponse`, `BaseSurface`, transport, routing, middleware,
`ServerWebhookBridge`) stays in `palm.common.runtimes.server`.

| Symbol | Before | After |
|---|---|---|
| `ServerContext` | `palm.common.runtimes.server.context` | `palm.runtimes.server.context` |
| `ServerApp`, `create_server_app` | `palm.common.runtimes.server.app` | `palm.runtimes.server.app` |

**Update imports:**

```python
# before
from palm.common.runtimes.server.context import ServerContext
from palm.common.runtimes.server.app import ServerApp, create_server_app
# after
from palm.runtimes.server.context import ServerContext
from palm.runtimes.server.app import ServerApp, create_server_app
```

`from palm.runtimes.server import ServerContext, ServerApp, create_server_app` (the
package re-export) is unchanged and remains the recommended import. Only code importing
the old `common.runtimes.server.*` submodule paths needs updating.

**Why:** `ServerContext` imported the entire service layer from inside `common`, which
(a) was the real shape of **PD-013** (a composition root misplaced in a low layer) and
(b) created a latent `services → server → ServerContext → services` import cycle. The
move removes both — the last non-sanctioned upward import edges in the tree.
