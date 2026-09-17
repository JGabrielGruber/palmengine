# Architecture Decision Records

Living index of Palm ADRs. Canonical folder: `docs/adr/`.  
Process: [AGENTS.md](../../AGENTS.md) §5 · template: [`.github/ISSUE_TEMPLATE/adr.md`](../../.github/ISSUE_TEMPLATE/adr.md) · library: [LIBRARY.md](../LIBRARY.md).

**Rule (0.52.5 / PD-020):** every significant architectural decision ships an ADR **or** an explicit waive recorded in the theme VISION / STATUS (why no ADR). Numbers are **append-only** — never renumber accepted ADRs to close a gap.

## Number gap

| Number | Status |
|--------|--------|
| **013** | **Unused — intentionally vacant.** See [013-number-reserved.md](013-number-reserved.md). Do not invent a retroactive decision to “fill” the hole. Next free integer after the latest accepted ADR. |

## Index

| ADR | Title | Status (header) |
|-----|--------|-----------------|
| [001](001-compositional-power-resources.md) | Compositional Power — Resource System Evolution (0.12) | Accepted |
| [002](002-pattern-apps-and-common-boundaries.md) | Pattern Apps and `palm.common` Boundaries | Accepted |
| [003](003-provider-apps.md) | Provider Apps and Django-Style Layout | Accepted |
| [004](004-cqrs-schemas-service-layer.md) | CQRS Schemas and Service Layer | Accepted |
| [005](005-service-domain-api.md) | Service Domain API (0.16) | Proposed\* |
| [006](006-assist-domain.md) | Assist Service Domain (0.18–0.19) | Accepted |
| [007](007-definition-revisioning.md) | Definition Revisioning & Migration (0.24) | Accepted |
| [008](008-design-service.md) | Design Service (0.25) | Accepted |
| [009](009-service-cqrs-contributors.md) | Service CQRS Contributors | Accepted |
| [010](010-prompt-state-interpolation.md) | Wizard Prompt State Interpolation (0.27) | Accepted |
| [011](011-local-document-resources.md) | Local Document & KV Resource Providers (0.28) | Accepted |
| [012](012-wizard-branch-step.md) | Wizard Branch Step (`step_kind: branch`) | Accepted |
| [013](013-number-reserved.md) | *(number reserved / unused)* | Vacant |
| [014](014-dashboard-definitions.md) | Dashboard Definitions (0.39) | Accepted |
| [015](015-technical-debt-baseline.md) | Technical-Debt Baseline & Audit Methodology (0.45) | Accepted |
| [016](016-ci-gate.md) | CI Quality Gate — NeonRoot hermetic checks (0.46) | Accepted |
| [017](017-import-seams.md) | Sanctioned import seams — closing T3 (0.47) | Accepted |
| [018](018-application-host-decomposition.md) | `ApplicationHost` decomposition strategy (0.48) | Accepted |
| [019](019-composition-profiles.md) | Composition profiles — declare the app's shape (0.50) | Accepted |
| [020](020-living-capabilities.md) | Living capabilities — third axis (0.51) | Accepted |
| [021](021-living-library.md) | The Living Library — SOURCE / BUILD / SURFACE (0.52) | Accepted |
| [022](022-neonroot-provider.md) | NeonRoot as a Palm provider — Sovereign Runners (0.53) | Accepted |
| [023](023-hermetic-jobs.md) | Hermetic jobs — NeonRoot as job runner, Palm as graph (0.54 replan) | Accepted |
| [024](024-workload-engine.md) | WorkloadEngine and the workload plane (0.56) | Accepted |
| [025](025-reactive-interests.md) | Reactive Interests — wait + trigger law (0.55) | Accepted |
| [026](026-palm-system-layer.md) | Palm system layer and module purposes (0.57) | Accepted |
| [027](027-session-plane.md) | Session plane — system glue, multi-instance (0.58) | Accepted |
| [028](028-system-boot.md) | System boot schedule + composition truth (0.59) | Accepted |
| [029](029-system-supervisor.md) | System supervisor + work plane on SystemInstance (0.60) | Accepted |
| [030](030-system-vitality.md) | System vitality — living-kernel observation (0.61) | Accepted |
| [031](031-multi-claimer-work-drain.md) | Multi-claimer work drain — exclusive claim first (0.62) | Accepted |
| [032](032-organism-assembly.md) | Organism assembly — DNA · admission · single readiness (0.63) | Accepted |
| [033](033-one-walker.md) | Old wiring dies in the same cut (0.64) | Accepted |
| [034](034-supervised-start-walks-registration.md) | Supervised start walks registration (0.65) | Accepted |
| [035](035-admission-sits-on-capabilities.md) | Admission sits on installed capabilities (0.66) | Accepted |
| [036](036-require-capability.md) | Require capability — dependents of the admission face (0.67) | Accepted |
| [037](037-navigator-invert.md) | Navigator invert — operator-guidance definition · presentation kit (0.69) | Proposed |

\*ADR-005 may be promoted to Accepted in a docs pass; shipped reality is the service domain API.

**Next free number:** 038.  
**Note:** System **0.57** through costume **0.68** **closed** (ADR-026…036 Accepted). Open minor: **0.69** Navigator ([ADR-037](037-navigator-invert.md) **Proposed**). Residual multi-process claim: [SD-019](../../TECH-DEBT.md#sd-019). Queue seeds: [VISION-TUNNELS](../vision/VISION-TUNNELS.md) · [VISION-SURFACE-DEFLATION](../vision/VISION-SURFACE-DEFLATION.md) · [VISION-TINY-LLM](../vision/VISION-TINY-LLM.md) · seed essay [VISION-ASSEMBLY](../vision/VISION-ASSEMBLY.md).

## How to add an ADR

1. Take the next free integer (`ls docs/adr/` — skip reserved vacancies).
2. Copy `.github/ISSUE_TEMPLATE/adr.md` → `docs/adr/NNN-short-slug.md`.
3. Status **Proposed** until the theme lands; then **Accepted** (or **Superseded** / **Rejected**).
4. Link from the theme `VISION-0.X.md`, and update **this index**.
5. If a change is significant but an ADR is **not** warranted (pure docs, pure rename with existing ADR, trivial fix): write one line in the VISION or STATUS slice — `ADR: waived — <reason>`.

## Out of band

Historical design notes and plans live under `docs/superpowers/` — they are **not** ADRs. Promote durable decisions into this folder when the choice becomes load-bearing.
