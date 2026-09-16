# Intended package map

**Status:** Stub. Target layout — refine as the architecture vault grows.

| Area | Intended home (sketch) | Notes |
|------|------------------------|--------|
| Pure structure | `palm.core.structure` | Reconciler + definition types |
| System structure | `palm.system.structure` | Manager, seat, hands, seed |
| Boot | `palm.system.boot` | Machine up |
| Planes / supervisor | `palm.system.subsystems…` | Traffic and continuous care |
| Product | `palm.services…` | Userland |
| Surfaces | `palm.runtimes…` | Transport |
| Present kit | `palm.kits.present` | Named (Navigator seed). Bind / present / submit / focus. Not shipped. |
| Embedded library surface | Runtime family `embedded` (library door). Not `EmbeddedRuntime`. | First present-kit adapter. Named, not shipped. |
| Host | `palm.app.host…` | Wire / packaging |

Add one note per package family when boundaries need prose (`core.md`, `system.md`, …).
