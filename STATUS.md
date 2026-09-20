# Palm Engine — Project Status

**Current Version:** `0.68.0` · **Active theme:** [**0.71** Place registry](docs/vision/VISION-0.71.md) · **Prior closed:** [**0.70** Authoring](docs/vision/closed/VISION-0.70.md)  
**Last Updated:** September 20, 2026 · José opened **0.71**. Floor through invert `0.71.0`–`0.71.15` **landed**; extra `0.71.16` stdlib settings **landed**; extra `0.71.17` embedded import isolation **landed**; extra `0.71.18` wheel omits surface static / MCP data **landed**. Names locked: `adopt` / `adopt:` / empty `runtime` / adopted rows stay `Workload`. ADR [039](docs/adr/039-place-registry-adopt.md) **Proposed**. Package stamp stays `0.68.0`. Spawn via `workload:` stays [0.63.16](docs/vision/closed/VISION-0.63.md). Assist stays until [surface deflation](docs/vision/VISION-SURFACE-DEFLATION.md).  
**Map:** [docs/PALM.md](docs/PALM.md) · open [VISION-0.71](docs/vision/VISION-0.71.md) · [ADR-039](docs/adr/039-place-registry-adopt.md) **Proposed** · scout [VISION-0.56](docs/vision/VISION-0.56.md) · closed [VISION-0.70](docs/vision/closed/VISION-0.70.md) · [ADR-038](docs/adr/038-authoring-adapter.md) **Accepted**  
**Debt (live):** [TECH-DEBT.md](TECH-DEBT.md) — **SD-025** (authoring job-leaf catalog write) · **SD-023** (0.68 exit residual) · **SD-024** (host names wizard) · **SD-020** (face paid; dependents paid) · **SD-021** · **SD-022** · residual **SD-019** · **SD-016** / **BI-*** / **SI-*** / **SU-***  
**Closed seasons:** [docs/vision/closed/](docs/vision/closed/) · [VERSIONING.md](docs/VERSIONING.md) (STATUS is the present)

### Agent resume (after compact)

Read: **this STATUS** → [VISION-0.71](docs/vision/VISION-0.71.md) (**open**) → [ADR-039](docs/adr/039-place-registry-adopt.md) **Proposed**.  
José opened 0.71 (2026-09-20). Plan `0.71.0`. Floor `0.71.1` adopt. Growth `0.71.2` projection. Compost `0.71.3` extra maps. Invert `0.71.4` typed book binds. Invert `0.71.5` typed `Workload` / `WorkloadHandle` book-row reads. Invert `0.71.6` typed `host_bind` (shell / engine / effects / spawn hands). Invert `0.71.7` typed `place_registry.engine_from_spawn` (`RegisteredPlaceSpawn`, no Protocol isinstance). Invert `0.71.8` typed adopt payload handle (no dict | `base_url` coercion). Compost `0.71.9` overlay (bare / `os:` no second map beside the book). Invert `0.71.10` typed `register_body` / `os_registry` (no `handles` bag / `__os_registry__`). Invert `0.71.11` StructureEngine place readiness via registry `ready` (no second observation body book). Invert `0.71.12` typed `workload_place` spec env at Mapping boundary (no `isinstance(..., dict)` silent drop). Invert `0.71.13` typed `WorkloadEngine` named runtime bind (no `isinstance(bound, dict)` / `isinstance(runtime, WorkloadRuntime)` soup). Invert `0.71.14` typed seat `bind_structure` on `StructureEffectPort` (no `getattr(self.effects, "bind_structure", None)`). Invert `0.71.15` drop StructureEngine `_places_ready` dual (readiness only via bound `ready` hand; unbound fail closed). Extra `0.71.16` stdlib `PalmSettings` + pip extra `dotenv` (José locked; empty hard deps). Extra `0.71.17` empty `palm.runtimes` surface barrel (embedded start does not load server/daemon/mcp). Extra `0.71.18` base wheel excludes SSR/Portal/Analytics `static/` and `mcp/data` (repo/sdist keep them; not a pip extra). **All landed through `0.71.18`.** José locked names (2026-09-20): method `adopt`, prefix `adopt:`, empty `runtime` on adopted rows, adopted rows stay `Workload`. Leftovers stay **named residual**: `workload_place` remaining `isinstance` (typed `WorkloadHandle` accept at Mapping body); `WorkloadEngine` remaining `isinstance` (argv-must-not-be-str); `place_spawn` remaining `getattr`/`isinstance` (`os:` process poll/pid/env payload). Do not reopen 0.56. Do not spawn as the floor (`workload:` already `0.63.16`). Do not implement Tiny LLM. Do not compost Assist. Do not add a `palm` `create_flow` `if` ([SD-025](TECH-DEBT.md#sd-025)). **Next:** José exit judgment plus named place leftovers. ADR-039 stays **Proposed**. Theme stays **open**.

| Spirit | Decision |
|--------|----------|
| **0.71 open** | Place registry. Adopt a named existing body. |
| **ADR-039** | **Proposed** |
| **ADR-038** | **Accepted** (0.70 closed) |
| **ADR-024** | Stays **Accepted** (workload engine scout) |
| **Names** | Locked: `adopt` / `adopt:` / empty `runtime` / `Workload` rows. |
| **Next** | José exit judgment. |
| **Later** | [TINY-LLM](docs/vision/VISION-TINY-LLM.md) · [SURFACE-DEFLATION](docs/vision/VISION-SURFACE-DEFLATION.md) · [SD-021](TECH-DEBT.md#sd-021) · [TUNNELS](docs/vision/VISION-TUNNELS.md) → [Grove](docs/vision/VISION-GROVE.md) |
| **Experimental** | Pre-1.0 · **no LTS** — [README](README.md) |

### Open theme 0.71 — slice guide

| Slice | Intent | Status |
|-------|--------|--------|
| **0.71.0** | Plan: VISION, ADR Proposed, STATUS, PALM pointer | landed |
| **0.71.1** | Adopt into the workload book; structure ENSURE; fail closed | landed |
| **0.71.2** | Structure registry projects the workload book | landed |
| **0.71.3** | Compost extra maps; place id is the book id | landed |
| **0.71.4** | Typed book binds; no handles duck-walk for bind discovery | landed |
| **0.71.5** | Typed `Workload` / `WorkloadHandle` book-row reads | landed |
| **0.71.6** | Typed `host_bind` shell / engine / effects / spawn hands | landed |
| **0.71.7** | Typed `place_registry` spawn / book bind (no Protocol isinstance) | landed |
| **0.71.8** | Typed adopt payload handle (no dict \| `base_url` coercion) | landed |
| **0.71.9** | Compost overlay; bare / `os:` no second map beside the book | landed |
| **0.71.10** | Invert `handles`; typed `register_body` / `os_registry` | landed |
| **0.71.11** | Invert StructureEngine place observations onto registry `ready` | landed |
| **0.71.12** | Typed `workload_place` spec env at Mapping boundary | landed |
| **0.71.13** | Typed `WorkloadEngine` initialize named runtime bind | landed |
| **0.71.14** | Typed seat `bind_structure` (`StructureEffectPort` match) | landed |
| **0.71.15** | Invert StructureEngine `_places_ready`; readiness only via ready hand | landed |
| **0.71.16** | Stdlib `PalmSettings`; empty hard deps; file load extra `dotenv` | landed |
| **0.71.17** | Empty `palm.runtimes` surface barrel; embedded start isolates from server | landed |
| **0.71.18** | Base wheel omits surface static / MCP data (keep in repo/sdist) | landed |

## Later seeds (not this season)

| Seed | Home |
|------|------|
| Surface compost | [VISION-SURFACE-DEFLATION](docs/vision/VISION-SURFACE-DEFLATION.md) |
| Profile / env structure duals | [SD-021](TECH-DEBT.md#sd-021) |
| Workload engine scout | [VISION-0.56](docs/vision/VISION-0.56.md) — remainder **adopt** is **0.71** |
| Tiny LLM (needs) | [VISION-TINY-LLM](docs/vision/VISION-TINY-LLM.md) — after 0.71 place |
| Tunnels → Grove | [VISION-TUNNELS](docs/vision/VISION-TUNNELS.md) → [VISION-GROVE](docs/vision/VISION-GROVE.md) |
