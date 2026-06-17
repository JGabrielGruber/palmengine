# Palm Engine — Project Status

**Current Version:** `0.12.9` (shipping)  
**Last Updated:** June 17, 2026  
**Maturity:** Compositional Power shipped — Resources are first-class; Palm Explorer includes full resource hub.

## Quick Overview

Palm is a lightweight, Python-first orchestration engine built on a clean **Behavior Tree** foundation. It excels at complex multi-step workflows, rich interactive wizards, compositional sub-flow orchestration, and transactional processes with durable state and human-in-the-loop participation.

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
- **Resource system (0.12)** — `ResourceDefinition`, `ResourceEngine`, `ResourceLeaf`, `ResourceCatalog`, `palm` provider
- Powerful Wizard pattern (validation, collection, transform, **resource** steps, parallel branches, backtracking, summary + commit)
- 22 built-in transform rules + extensible `TransformEngine` (`enrich_resource` with `resource_ref`)
- Layered state schemas + scoped execution state
- Durable process instances with resume across restarts
- CQRS (Command + Query buses + projections including `resource_invocations`)
- Reliability primitives: Transactional outbox, Compensation handlers (resource undo), Webhook dispatch support
- Composable host roles (`ApplicationHost` + `HostProfile`)
- Rich CLI + REPL with live dashboard (`palm status`) and `palm resource *` commands
- Multiple runtimes (Embedded, Daemon, Server, CLI)
- **Palm Explorer** — SSR hub at `/explorer` (flows, jobs, instances, **resources**); `GET /` redirects here

## 0.12 — Compositional Power (Shipped)

**Vision document:** [docs/VISION-0.12.md](docs/VISION-0.12.md)  
**Migration:** [MIGRATION-0.12.md](MIGRATION-0.12.md)  
**ADR:** [docs/adr/001-compositional-power-resources.md](docs/adr/001-compositional-power-resources.md)  
**Release checklist:** [RELEASE-0.12.9.md](RELEASE-0.12.9.md)

| Component | Status |
|-----------|--------|
| `ResourceDefinition` + repository | ✅ Shipped |
| `ResourceEngine` / `BaseProvider` evolution | ✅ Shipped |
| `ResourceLeaf` (core BT node) | ✅ Shipped |
| `palm` provider (local + remote recursion) | ✅ Shipped |
| Transform / compensation / observability integration | ✅ Shipped |
| Explorer resources hub + release polish | ✅ Shipped |

## Areas Under Active Improvement

- WebSocket runtime surface for live wizard/job streaming
- Further tightening of public API surface (`__all__` declarations are consistent but `palm/__init__.py` remains intentionally minimal)
- Saga-style compensation patterns beyond single-resource undo
- KernelLeaf / GPU execution research (non-goal for 0.12)

## Known Limitations & Technical Debt

- Documentation consistency enforced via `just docs-check` (wired into `just release-prep`)
- Some `__init__.py` files use lazy `__getattr__` exports — intentional for import performance
- Legacy v0.6 flat-file storage support still exists (intentional for migration compatibility)
- Projection rebuild strategy for very large instance counts is basic (batch + skip-if-fresh)
- Standalone `ServerRuntime` may return empty resource invocation rows when projections aren't wired

## Documentation Health

| Document              | Status          | Notes |
|-----------------------|------------------|-------|
| `README.md`           | Good            | 0.12 highlights + Resource Best Practices |
| `ARCHITECTURE.md`     | Good            | Resource layer shipped section |
| `docs/VISION-0.12.md` | Good            | All phases complete |
| `MIGRATION-0.12.md`   | Good            | Breaking changes + compensation + cache + Explorer |
| `docs/adr/001-*.md`   | Good            | Resource evolution ADR |
| `DEVELOPMENT.md`      | Good            | Contributor guide |
| `AGENTS.md`           | Good            | Constitution aligned with 0.12 |
| `MIGRATION-0.10.md`   | Excellent       | Upgrade path from 0.9.x |
| `docs/index.html`     | Good            | 0.12.9 with Compositional Power highlights |
| `docs/llms.txt`       | Good            | AI context guide updated for 0.12 |
| `CHANGELOG.md`        | Good            | `[0.12.9]` section complete |

## Priorities & Next Steps

1. Publish `0.12.9` to PyPI (`just release-prep` → tag → publish)
2. WebSocket surface and richer server auth
3. KernelLeaf / GPU execution research
4. Pipeline/DAG resource stage builders (deferred from Phase 3)

## Useful Links

- [CHANGELOG.md](CHANGELOG.md)
- [MIGRATION-0.12.md](MIGRATION-0.12.md)
- [MIGRATION-0.10.md](MIGRATION-0.10.md)
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [AGENTS.md](AGENTS.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)
- [SCOPE.md](SCOPE.md)
- [docs/VISION-0.12.md](docs/VISION-0.12.md)
- Examples: `examples/README.md`

## How to Contribute

Follow the guidance in [DEVELOPMENT.md](DEVELOPMENT.md) and [AGENTS.md](AGENTS.md).  
All significant architectural changes should be accompanied by an ADR and documentation updates.