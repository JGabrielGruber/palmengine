# Palm Engine — Project Status

**Current Version:** `0.11.8`  
**Last Updated:** June 17, 2026  
**Maturity:** Architecture stabilized. Palm Explorer shipped; documentation and website aligned with 0.11.8.

## Quick Overview

Palm is a lightweight, Python-first orchestration engine built on a clean **Behavior Tree** foundation. It excels at complex multi-step workflows, rich interactive wizards, and transactional processes with durable state and human-in-the-loop participation.

**Distribution name:** `palmengine` (PyPI)  
**Import name:** `palm`  
**Recommended entrypoint:** `ApplicationHost` via `create_cli_host()` for CLI, or `ApplicationHost(profile=HostProfile.all_in_one())` for library use

## Architecture Snapshot

Palm follows a **layered, registry-driven** model with a strictly pure core:

- `palm/core/` — Pure foundational engines (Behavior Tree, Orchestration, Context, Storage, Resource, Event, Auth, Transform). **Zero external Palm imports allowed.**
- `palm/common/` — Rich shared coordination layer (executions, plans, hooks, persistence, CQRS, compensation, transforms, runtime infrastructure).
- `palm/app/` — Application orchestration. `ApplicationHost` is the primary recommended orchestrator; `PalmApp` is infrastructure.
- `palm/patterns/`, `palm/providers/`, `palm/storages/` — Extensible plugin-style apps.
- `palm/runtimes/` — Thin surfaces over the common runtime layer.

See [ARCHITECTURE.md](ARCHITECTURE.md) and [AGENTS.md](AGENTS.md) for full details and rules.

## Key Capabilities (Mature)

- Behavior Tree execution engine
- Powerful Wizard pattern (validation, collection steps, transform steps, parallel branches, backtracking, summary + transactional commit)
- 22 built-in transform rules + extensible `TransformEngine`
- Layered state schemas + scoped execution state
- Durable process instances with resume across restarts
- CQRS (Command + Query buses + projections)
- Reliability primitives: Transactional outbox, Compensation handlers, Webhook dispatch support
- Composable host roles (`ApplicationHost` + `HostProfile`)
- Rich CLI + REPL with live dashboard (`palm status`)
- Multiple runtimes (Embedded, Daemon, Server, CLI)
- **Palm Explorer** — SSR hub at `/explorer` (flows, jobs, instances, schemas); `GET /` redirects here

## Recent Freshness Work (June 2026)

**0.11.8 polish release:**

- **Palm Explorer** — living server hub replaces legacy wiki/docs paths; flow submission UX refined
- **Root redirect** — `GET /` → `/explorer`; health includes `home`
- **Website (`docs/index.html`)** — hero, quickstart, and REST section highlight Explorer

Documentation refinement pass (ApplicationHost release):

- **Website (`docs/index.html`)** — JSON-LD, meta tags, hero badge, and feature highlights updated; ApplicationHost and CQRS surfaced prominently
- **`docs/llms.txt`** — Expanded into a high-quality AI agent context guide (architecture, entry points, invariants, extension patterns)
- **`README.md`** — Removed stale version stamp from Transforms section heading
- **`ARCHITECTURE.md`** — Transform rule count clarified (22 built-in rules)
- **`PalmApp` module docstring** — Aligned with infrastructure-layer role

## Areas Under Active Improvement

- Lightweight automation for version + documentation consistency at release time
- Further tightening of public API surface (`__all__` declarations are consistent but `palm/__init__.py` remains intentionally minimal)
- Potential deeper integration between TransformEngine and ResourceEngine
- Ongoing evolution of compensation and saga-style patterns

## Known Limitations & Technical Debt

- Documentation consistency enforced via `just docs-check` (wired into `just release-prep`)
- Some `__init__.py` files use lazy `__getattr__` exports — intentional for import performance; document in DEVELOPMENT.md when touched
- Legacy v0.6 flat-file storage support still exists (intentional for migration compatibility)
- Projection rebuild strategy for very large instance counts is basic (batch + skip-if-fresh)
- `just palm-demo-onboard` still uses `wizard start` alias (valid; `flow start` is the recommended phrase)

## Documentation Health

| Document              | Status          | Notes |
|-----------------------|------------------|-------|
| `README.md`           | Good            | ApplicationHost recommended; Palm Explorer documented |
| `ARCHITECTURE.md`     | Good            | Reflects current layers and reliability primitives |
| `DEVELOPMENT.md`      | Good            | Contributor guide solid; ApplicationHost bootstrap documented |
| `AGENTS.md`           | Good            | Constitution aligned with 0.10+ |
| `MIGRATION-0.10.md`   | Excellent       | Clear upgrade path from 0.9.x |
| `docs/index.html`     | Good            | Updated to 0.11.8 with Palm Explorer highlights |
| `docs/llms.txt`       | Good            | Rich AI context guide |
| `examples/README.md`  | Good            | Host-backed CLI paths documented |

## Public API Surface Notes

| Module | `__all__` pattern | Notes |
|--------|-------------------|-------|
| `palm` | `["__version__"]` only | Intentionally minimal top-level surface |
| `palm.app` | Explicit + lazy `ApplicationHost`, `run_host` | Recommended import path |
| `palm.common` | Explicit + lazy coordination exports | Well-structured |
| `palm.app.host` | Explicit + lazy `ApplicationHost`, `run_host` | Mirrors `palm.app` lazy pattern |
| Plugin apps | Per-subpackage `registry` + `__all__` | Consistent Django-style layout |

## Priorities & Next Steps

1. Extend `just docs-check` with optional link validation when needed
2. Continue maturing reliability features (compensation patterns, webhook consumers)
3. Explore deeper Knowledge Graph integration (Knowkey) for architecture documentation
4. Consider ADR for documentation freshness automation when implemented

## Useful Links

- [CHANGELOG.md](CHANGELOG.md)
- [MIGRATION-0.10.md](MIGRATION-0.10.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [AGENTS.md](AGENTS.md) — Constitution for agents and contributors
- [DEVELOPMENT.md](DEVELOPMENT.md)
- [SCOPE.md](SCOPE.md)
- Examples: `examples/README.md`

## How to Contribute

Follow the guidance in [DEVELOPMENT.md](DEVELOPMENT.md) and [AGENTS.md](AGENTS.md).  
All significant architectural changes should be accompanied by an ADR and documentation updates.