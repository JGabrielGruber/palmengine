# ADR-039 — Place registry adopt (named existing body)

**Status:** Proposed  
**Date:** 2026-09-20  
**Theme:** [VISION-0.71](../vision/VISION-0.71.md) (**open**)  
**Scout:** [VISION-0.56](../vision/VISION-0.56.md) · [ADR-024](024-workload-engine.md) **Accepted**  
**Spawn hand:** [ADR-032](032-organism-assembly.md) **Accepted** (`0.63.16` `workload:`)  
**Map:** [PALM.md](../PALM.md)

José opened theme **0.71** (2026-09-20). Floor: adopt a named place. Package stamp stays `0.68.0`. Accept at theme exit.

---

## Context

1. [ADR-024](024-workload-engine.md) put isolation on a pure `WorkloadEngine` and runners. That foundation landed.  
2. [ADR-032](032-organism-assembly.md) lets structure **require** places. `0.63.16` routes `workload:` through `WorkloadPlaceSpawn` (fail closed if unbound). Bare ids still succeed in-process with no body.  
3. [PALM.md](../PALM.md) names the **place registry** as the workload-plane book of named places (spawn or adopt). Vision still says place book as teaching.  
4. [VISION-TINY-LLM](../vision/VISION-TINY-LLM.md) needs a small long-lived service as a place. First speak may be a URL that is **already up**. Adopt is how that stays honest. Speak is not this ADR.  
5. Reopening 0.56 would treat ssh/k8s/peer/blueprints as this season’s subject. José named a new minor **0.71** instead.

## Decision

### D1 — New minor 0.71

Place-registry **adopt** is theme **0.71**. [VISION-0.56](../vision/VISION-0.56.md) stays the engine scout. Do not reuse 0.56 patch numbers.

### D2 — Truth home of bodies is the workload plane

Spawned and adopted places live in the **workload** book. Structure `PlaceEffectPort` / `InProcessPlaceRegistry` is the **hand** and a **projection** of readiness. It is not a second truth home for bodies.

### D3 — Floor is adopt

Floor: record an existing body as a named place with a handle. Existing `WorkloadHandle.base_url` is enough. No runner `start`. Missing handle fails closed.

Spawn via `workload:` is already `0.63.16`. It is not the floor.

### D4 — Hands route on the existing table

Adopt is a **registered strategy** on `RegisteredPlaceSpawn`. Locked prefix: `adopt:`. Method: `WorkloadEngine.adopt`. Adopted rows stay `Workload` with empty `runtime` (no fake runner name). Do not add a one-name `if` on the spawn port. Do not add a `PlaceService`.

### D5 — Palm did not create an adopted body

Release / ENSURE gone for an adopted place **unbinds**. It does not kill a process Palm did not start.

### D6 — Tiny LLM is not this theme

A later provider **speaks**. A later definition builds arguments. This ADR only makes the **place** meanable. No model-driver plugin.

### D7 — Stamp

Package version stays `0.68.0` until José cuts an embedded release.

## Consequences

- Tests can adopt a URL-shaped place and assemble DNA that requires it without spawning.  
- Bare in-process place ids stay until a later compost. Name them. Do not “fix” them to keep adopt green.  
- Product CQRS `workload.adopt` is growth, not floor.

## Status

**Proposed** until José exits 0.71 and accepts this ADR.
