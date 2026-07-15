# Reactive Data Plane 0.45.x Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans per sub-release.

**Goal:** Close inbound→pipeline data-plane gaps, add same-process ingress, then ship system watchdog + coconut migration as proofs.

**Architecture:** Metadata (ops) and state (blackboard) are separate submission planes. Internal inbound before examples — no loopback dogfood.

**Spec:** [docs/VISION-0.45.md](../../VISION-0.45.md) · [design spec](../specs/2026-07-15-reactive-data-plane-design.md)

---

## Release train

| Version | Phase | Content |
|---------|-------|---------|
| 0.45.0 | — | Vision + spec + this plan |
| 0.45.1 | A | metadata/state, seed_state, append_item, put_resource |
| 0.45.2 | C | same-process inbound (internal mode or on_event) |
| 0.45.3 | B | system watchdog definitions + coconut slice |

---

# 0.45.0 — Docs (complete when committed)

- [x] [docs/VISION-0.45.md](../../VISION-0.45.md)
- [x] [design spec](../specs/2026-07-15-reactive-data-plane-design.md)
- [x] This plan
- [ ] Version bump `0.45.0`
- [ ] Commit

---

# 0.45.1 — Phase A: Data plane

### Task 1: flow_command metadata + state

**Files:** [service.py](../../../src/palm/services/execution/flows/service.py), [jobs.py](../../../src/palm/runtimes/server/surfaces/rest/handlers/jobs.py), [in_process.py](../../../src/palm/runtimes/mcp/in_process.py)

- [ ] Test: `tests/test_flow_command_metadata_0_45.py`
- [ ] Implement pass-through; DRY jobs handler
- [ ] MCP submit_flow forwards metadata/state

### Task 2: coerce_job_state

**Files:** Create [job_state.py](../../../src/palm/common/executions/job_state.py), modify [flow_submission.py](../../../src/palm/common/executions/flow_submission.py)

- [ ] Test: dict → BlackboardState in submission

### Task 3: work.seed_state

**Files:** [inbound.py](../../../src/palm/common/resource/inbound.py), create [seed_state.py](../../../src/palm/common/work/seed_state.py), [inbound_service.py](../../../src/palm/app/host/inbound_service.py), [application_host.py](../../../src/palm/app/host/application_host.py)

- [ ] Test: `tests/test_work_seed_state_0_45.py`
- [ ] Test: `tests/test_work_drain_seed_0_45.py` (integration)

### Task 4: append_item

**Files:** Create [append_item.py](../../../src/palm/common/transforms/rules/append_item.py), [registry.py](../../../src/palm/common/transforms/rules/registry.py), [engine.py](../../../src/palm/core/transform/engine.py)

- [ ] Test: `tests/test_append_item_transform_0_45.py`

### Task 5: put_resource

**Files:** Create [put_resource.py](../../../src/palm/common/transforms/rules/put_resource.py), register

- [ ] Test: `tests/test_put_resource_transform_0_45.py`

### Task 6: Release 0.45.1

- [ ] `pytest tests/test_*_0_45*.py`
- [ ] `just guard-common`
- [ ] Version + commit

---

# 0.45.2 — Phase C: Same-process ingress (shipped)

### Task 7: internal inbound mode

- [x] `mode: internal` on `metadata.inbound`
- [x] `InboundBindingService` subscribes to host `EventEngine` (`*`)
- [x] `event_types` filter; envelope + WorkIntent without loopback
- [x] `tests/test_inbound_internal_0_45_2.py`

---

# 0.45.3 — Phase B: Examples + migrations

### Task 9: System event-watch pack

**Files:** `examples/definitions/system/event_watch_*.py`, dashboard tile

- [ ] Resources: inbox, log, watch (internal inbound)
- [ ] Pipeline flow: map_fields → append_item → put_resource
- [ ] Test: `tests/test_system_event_watch_0_45_3.py`

### Task 10: Coconut pipeline slice

- [ ] Migrate one non-interactive wizard chain → pipeline

### Task 11: Release 0.45.3

- [ ] Version + commit