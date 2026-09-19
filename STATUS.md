# Palm Engine — Project Status

**Current Version:** `0.68.0` · **Active theme:** [**0.70** Authoring](docs/vision/VISION-0.70.md) · **Prior closed:** [**0.69** Navigator](docs/vision/closed/VISION-0.69.md)  
**Last Updated:** September 19, 2026 · José opened **0.70** (2026-09-19). Plan `0.70.0`. Adapter `0.70.1`. Present start `0.70.2`. Pack `0.70.3`. Thin apply `0.70.4`. ADR [038](docs/adr/038-authoring-adapter.md) **Proposed**. Package stamp stays `0.68.0`. Assist stays until [surface deflation](docs/vision/VISION-SURFACE-DEFLATION.md). Theme **stays open**.  
**Map:** [docs/PALM.md](docs/PALM.md) · [VISION-0.70](docs/vision/VISION-0.70.md) · seed [VISION-AUTHORING](docs/vision/VISION-AUTHORING.md) · [ADR-038](docs/adr/038-authoring-adapter.md) **Proposed** · [MIGRATION-0.70](docs/migrations/MIGRATION-0.70.md) · closed [VISION-0.69](docs/vision/closed/VISION-0.69.md) · [ADR-037](docs/adr/037-navigator-invert.md) **Accepted**  
**Debt (live):** [TECH-DEBT.md](TECH-DEBT.md) — **SD-023** (0.68 exit residual) · **SD-024** (host names wizard) · **SD-020** (face paid; dependents paid) · **SD-021** · **SD-022** · residual **SD-019** · **SD-016** / **BI-*** / **SI-*** / **SU-***  
**Closed seasons:** [docs/vision/closed/](docs/vision/closed/) · [VERSIONING.md](docs/VERSIONING.md) (STATUS is the present)

### Agent resume (after compact)

Read: **this STATUS** → [VISION-0.70](docs/vision/VISION-0.70.md) (**open**, **§11 remaining direction**) → [VISION-AUTHORING](docs/vision/VISION-AUTHORING.md) (locks) → [ADR-038](docs/adr/038-authoring-adapter.md) **Proposed**.  
José opened 0.70 (2026-09-19). Package **`palm.kits.authoring`**. Floor `0.70.1`–`0.70.2` is real. Pack/apply `0.70.3`–`0.70.4` is half-done (pytest is the leaf). Theme is a seed, not a sealed slice table. José exits. Do not stamp `INTENTION_KITS`. Do not grow land verbs on present. Do not require Design on `embedded()`. Do not compost Assist. Do not pay [SD-024](TECH-DEBT.md#sd-024).

| Spirit | Decision |
|--------|----------|
| **0.70 open** | Authoring adapter. Land a shape on embedded `definitions`. |
| **ADR-038** | **Proposed** (accept at exit) |
| **Floor** | One-shot commit via adapter on `CompositionProfile.embedded()`; present starts it |
| **0.70.1** | `palm.kits.authoring` in `INSTALLED_KITS`. `land` / `commit` walks `create_flow`. |
| **0.70.2** | Present starts the committed catalog id. Tests: `tests/test_authoring_present_start_0_70_2.py`. |
| **0.70.3** | Authoring pack wizard. As-built `authoring-pack`. Pack id unnamed. Tests: `tests/test_authoring_pack_0_70_3.py`. |
| **0.70.4** | Thin apply speaks a file snapshot. Leaf `land().commit`; resource via `create_resource`; present drives. Tests: `tests/test_authoring_apply_snapshot_0_70_4.py`. |
| **Next** | Explore remaining direction: [VISION-0.70 §11](docs/vision/VISION-0.70.md). Job leaf speaks the adapter. Do not add another fixture wizard. |
| **0.69 closed** | Navigator invert. Guidance is a definition. Kit walks. |
| **ADR-037** | **Accepted** |
| **ADR-006** | Stays **Accepted** (as-built Assist) |
| **Later** | [SURFACE-DEFLATION](docs/vision/VISION-SURFACE-DEFLATION.md) · [SD-021](TECH-DEBT.md#sd-021) · [VISION-0.56](docs/vision/VISION-0.56.md) · [TINY-LLM](docs/vision/VISION-TINY-LLM.md) · [TUNNELS](docs/vision/VISION-TUNNELS.md) → [Grove](docs/vision/VISION-GROVE.md) |
| **Experimental** | Pre-1.0 · **no LTS** — [README](README.md) |

## Later seeds (not this season)

| Seed | Home |
|------|------|
| Surface compost | [VISION-SURFACE-DEFLATION](docs/vision/VISION-SURFACE-DEFLATION.md) |
| Profile / env structure duals | [SD-021](TECH-DEBT.md#sd-021) |
| Workload place book | [VISION-0.56](docs/vision/VISION-0.56.md) (scout; remainder queued) |
| Tiny LLM (needs) | [VISION-TINY-LLM](docs/vision/VISION-TINY-LLM.md) — after Navigator walk + 0.56 place |
| Tunnels → Grove | [VISION-TUNNELS](docs/vision/VISION-TUNNELS.md) → [VISION-GROVE](docs/vision/VISION-GROVE.md) |
