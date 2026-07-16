# Scout: 0.51.6 — the ServerContext fold-in (read-only assessment)

*A scouting spike, not a plan. Evidence gathered before committing to (or declining) the
fold-in that [ADR-019](adr/019-composition-profiles.md) / [0.50.5f](VISION-0.50.md) left
"reachable once a lean `ApplicationHost` exists" — which [0.51.5](VISION-0.51.md) now
delivers.*

## The question

Now that `ApplicationHost` can express the lean, projection-less shape (0.51.5), should
`ServerContext` fold into it — one assembler behind all server surfaces — or does it stay?

## What the code shows

### Finding A — the surface protocol is small, but 3 gaps reveal why `ServerContext` exists

Across the ~50 REST/WS/MCP/SSR files, surfaces touch a `ServerContext` through exactly **12
members**: `definitions` (19), `execution` (16), `runtime` (15), `assist` (11), `design`
(9), `execute` (6), `ask` (6), `analytics` (6), `schemas` (5), `wait_until_idle` (4),
`system` (4), `host` (2).

`ApplicationHost` already satisfies **9 of the 12** directly. The other three are the crux:

- **`ctx.runtime` (15 uses) — property vs method.** Surfaces use it as a *property*
  returning *the one server runtime* (`ctx.runtime.version` / `.repository` / `.get_job` /
  `.orchestration`). But `ApplicationHost.runtime(name)` is a *method*, and **must stay
  one** — the host is multi-runtime and routes by name (`_resolve_execution_runtime` →
  `app.runtime(resolved)`). Surfaces therefore need a *single-runtime view*. That view **is
  `ServerContext`.**
- **`wait_until_idle` (4 uses)** — not on `ApplicationHost` at all.
- **`ctx.host` (2 uses)** — a self-reference (`runtime.application_host = ctx.host`) that only
  means something when the context and the host are *distinct* objects.

Eliminating the `ServerContext` type forces a bad trade: either **pollute `ApplicationHost`**
with surface-shaped API (a no-arg `runtime` property that breaks multi-runtime, plus
`wait_until_idle`) — muddying the assembler — or **keep a thin adapter** that presents the
single-runtime view… which is `ServerContext` under a new name. Neither is a simplification.

### Finding B — the read-side reuse is genuinely clean

`StandaloneQueryHandlers` (`common/runtimes/server/cqrs.py`) already serve every read
direct-from-runtime off a single `self._runtime` (`get_job`, `instance_manager`,
`repository`, `orchestration`, …). A lean (single-runtime) `ApplicationHost` could wire
`StandaloneQueryHandlers(host.runtime())` when `not composition.has("projections")` — giving
it **read-completeness with zero surface or `ServerContext` changes**.

## Recommendation

The fold-in splits into two very different halves:

| Half | Cost | Value | Verdict |
|---|---|---|---|
| **Read-side**: lean `ApplicationHost` serves reads via `StandaloneQueryHandlers` reuse | Low, contained (inside `_wire_cqrs`) | Real — finishes the lean host (submit **and** read complete) | **Worth doing** |
| **Type-elimination**: re-type ~50 surfaces off `ServerContext` onto the host | High, caller-facing, needs a runtime-view either way | ~None — reintroduces the view it removes | **Not worth doing** |

So the evidence *confirms and sharpens* 0.50.5f: **`ServerContext` stays** (the surface-facing
single-runtime view is its reason to exist, now proven by the `runtime` property/method gap),
and the genuinely valuable step is the contained read-side completion.

**Proposed 0.51.6 (contained):** when a composition omits `projections`, wire
`StandaloneQueryHandlers` over the host's primary runtime so a lean `ApplicationHost` is
read-complete — no surface churn, no `ServerContext` removal. Guard: it assumes a
single-runtime lean host; multi-runtime-lean stays out of scope (log if encountered).

**Alternative:** declare 0.51 complete at the capability work; leave the read-side as a
documented, reachable follow-up. The lean host is already submit-complete and *starts*, which
was the theme's stated payoff.
