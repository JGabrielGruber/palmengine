# Palm Engine — Project Status

**Current Version:** `0.10.9`  
**Last Updated:** June 16, 2026  
**Maturity:** Architecture stabilized. Documentation and website refresh in progress.

## Quick Overview

Palm is a lightweight, Python-first orchestration engine built on a clean **Behavior Tree** foundation. It excels at complex multi-step workflows, rich interactive wizards, and transactional processes with durable state and human-in-the-loop participation.

**Distribution name:** `palmengine` (PyPI)  
**Import name:** `palm`  
**Recommended entrypoint:** `ApplicationHost` (with `HostProfile`)

## Architecture Snapshot

Palm follows a **layered, registry-driven** model with a strictly pure core:

- `palm/core/` — Pure foundational engines (Behavior Tree, Orchestration, Context, Storage, Resource, Event, Auth, Transform). **Zero external Palm imports allowed.**
- `palm/common/` — Rich shared coordination layer (executions, plans, hooks, persistence, CQRS, compensation, transforms, runtime infrastructure).
- `palm/app/` — Application orchestration. `ApplicationHost` is the primary recommended orchestrator.
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

## Areas Under Active Improvement

- Documentation refresh and website update (current priority)
- Living project summary and knowledge management (`STATUS.md`, `llms.txt`, ADRs)
- Further tightening of public API surface and `__all__` declarations
- Potential deeper integration between TransformEngine and ResourceEngine
- Ongoing evolution of compensation and saga-style patterns

## Known Limitations & Technical Debt

- Website structured data and some meta information still reference older versions (being updated)
- Some `__init__.py` files have inconsistent `__all__` exports
- Legacy v0.6 flat-file storage support still exists (intentional for migration compatibility)
- No automated enforcement yet for documentation consistency during releases
- Projection rebuild strategy for very large instance counts is basic (batch + skip-if-fresh)

## Documentation Health

| Document              | Status          | Notes |
|-----------------------|------------------|-------|
| `README.md`           | Good            | Up to date with 0.10 |
| `ARCHITECTURE.md`     | Good            | Reflects current layers |
| `DEVELOPMENT.md`      | Good            | Contributor guide solid |
| `AGENTS.md`           | Recently updated| Now aligned with 0.10+ |
| `MIGRATION-0.10.md`   | Excellent       | Very clear upgrade path |
| `docs/index.html`     | Needs update    | Structured data still on 0.9.7 |
| `docs/llms.txt`       | Basic           | Functional but can be richer |
| Examples              | Good            | Well documented |

## Priorities & Next Steps

1. Complete documentation & website refresh (including `STATUS.md`)
2. Establish lightweight automation for version + documentation consistency
3. Continue maturing reliability features (compensation patterns, webhook consumers)
4. Explore deeper Knowledge Graph integration (Knowkey) for the project’s own architecture

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
