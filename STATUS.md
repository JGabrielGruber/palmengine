# Palm Engine — Project Status

**Current Version:** `0.68.0` · **Active theme:** [**0.71** Place registry](docs/vision/VISION-0.71.md) · **Prior closed:** [**0.70** Authoring](docs/vision/closed/VISION-0.70.md)  
**Last Updated:** September 20, 2026 · José opened **0.71**. Floor through invert `0.71.0`–`0.71.7` **landed**. ADR [039](docs/adr/039-place-registry-adopt.md) **Proposed**. Package stamp stays `0.68.0`. Spawn via `workload:` stays [0.63.16](docs/vision/closed/VISION-0.63.md). Assist stays until [surface deflation](docs/vision/VISION-SURFACE-DEFLATION.md).  
**Map:** [docs/PALM.md](docs/PALM.md) · open [VISION-0.71](docs/vision/VISION-0.71.md) · [ADR-039](docs/adr/039-place-registry-adopt.md) **Proposed** · scout [VISION-0.56](docs/vision/VISION-0.56.md) · closed [VISION-0.70](docs/vision/closed/VISION-0.70.md) · [ADR-038](docs/adr/038-authoring-adapter.md) **Accepted**  
**Debt (live):** [TECH-DEBT.md](TECH-DEBT.md) — **SD-025** (authoring job-leaf catalog write) · **SD-023** (0.68 exit residual) · **SD-024** (host names wizard) · **SD-020** (face paid; dependents paid) · **SD-021** · **SD-022** · residual **SD-019** · **SD-016** / **BI-*** / **SI-*** / **SU-***  
**Closed seasons:** [docs/vision/closed/](docs/vision/closed/) · [VERSIONING.md](docs/VERSIONING.md) (STATUS is the present)

### Agent resume (after compact)

Read: **this STATUS** → [VISION-0.71](docs/vision/VISION-0.71.md) (**open**) → [ADR-039](docs/adr/039-place-registry-adopt.md) **Proposed**.  
José opened 0.71 (2026-09-20). Plan `0.71.0`. Floor `0.71.1` adopt. Growth `0.71.2` projection. Compost `0.71.3` extra maps. Invert `0.71.4` typed book binds. Invert `0.71.5` typed `Workload` / `WorkloadHandle` book-row reads. Invert `0.71.6` typed `host_bind` (shell / engine / effects / spawn hands). Invert `0.71.7` typed `place_registry.engine_from_spawn` (`RegisteredPlaceSpawn`, no Protocol isinstance). **All landed.** Leftovers stay **named residual**: `RegisteredPlaceSpawn.handles` (place-id body handles + `__os_registry__` stash), StructureEngine place observations (assemble/admission), overlay (bare ids and `os:` until a later body strategy), EffectIntent payload handle coercion (`WorkloadHandle` | dict | `base_url`). Do not reopen 0.56. Do not spawn as the floor (`workload:` already `0.63.16`). Do not implement Tiny LLM. Do not compost Assist. Do not add a `palm` `create_flow` `if` ([SD-025](TECH-DEBT.md#sd-025)). Working prefix `adopt:` until José locks. **Next:** José locks `adopt` / `adopt:` and exit judgment. No queued further compost.

| Spirit | Decision |
|--------|----------|
| **0.71 open** | Place registry. Adopt a named existing body. |
| **ADR-039** | **Proposed** |
| **ADR-038** | **Accepted** (0.70 closed) |
| **ADR-024** | Stays **Accepted** (workload engine scout) |
| **Next** | José locks `adopt` / `adopt:` · exit judgment. |
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

## Later seeds (not this season)

| Seed | Home |
|------|------|
| Surface compost | [VISION-SURFACE-DEFLATION](docs/vision/VISION-SURFACE-DEFLATION.md) |
| Profile / env structure duals | [SD-021](TECH-DEBT.md#sd-021) |
| Workload engine scout | [VISION-0.56](docs/vision/VISION-0.56.md) — remainder **adopt** is **0.71** |
| Tiny LLM (needs) | [VISION-TINY-LLM](docs/vision/VISION-TINY-LLM.md) — after 0.71 place |
| Tunnels → Grove | [VISION-TUNNELS](docs/vision/VISION-TUNNELS.md) → [VISION-GROVE](docs/vision/VISION-GROVE.md) |
