# Migration — 0.67 Dependents require the organ

**Theme:** [VISION-0.67](../vision/closed/VISION-0.67.md) (**closed**) · **ADR:** [036](../adr/036-require-capability.md) **Accepted**  
**Map:** [PALM.md](../PALM.md)

Palm is pre-1.0. Theme closed at stamp `0.67.0`. Additive: a new require beside the ready door. Costume composted: [VISION-0.68](../vision/closed/VISION-0.68.md) (**closed**). Residual [SD-023](../../TECH-DEBT.md#sd-023).

## Prefer

| Goal | Use |
|------|-----|
| May business that needs ground run? | `require_business_admission(source)` (unchanged) |
| Is this organ here (and is the organism ready)? | `require_capability(source, name)` |
| Query without raise | `admission.has_capability(name)` |
| Work-plane drain query | install-board `able()` (ready then `work_drain`) |
| Wait / continue query | `admission_able()` / `may_run_business` |

## Behavior / names that will change

| Was | Now (from 0.67.1) |
|-----|-------------------|
| Organ require = dig structure or pretend ready is membership | `require_capability(source, name)` |
| Missing organ | `CapabilityRefusedError` after the ready wall |
| Missing organ on a surface | REST/MCP **409** `capability_refused`; CLI/SSR/WS brand (0.67.4) |

`require_business_admission` still fail-closes only on `may_run_business`. Existing call sites need no change.

`able` on the install board stays zero-arg. From 0.67.2 the default closure also reads `work_drain`. Wait uses a ready-only closure. From 0.67.3 host spawn injects drain `install_able` and ready `install_admission_able` (both include host `_started`). Decorators are not added.

From 0.67.4 surfaces speak `capability_refused` for the organ door. Ready-false stays `admission_refused`. Do not mix the codes.

From 0.67.5 `tick_schedules` (and host `tick_work` with `schedules=True`) uses the same drain able as `tick`. Ready without `work_drain` does not enqueue due schedules or advance `next_fire_at`. Direct `ScheduleRegistry.tick` stays a store helper.

From 0.67.6 vitality `work_cycle` drain proofs use `local.cli`. Embedded ready still enqueues; tick does not process.

From 0.67.7 `journal` membership is the structure definition list. Host attach follows `has_capability("journal")`. Composition omit does not hide a listed name. `local.embedded` and `local.worker` omit the organ. Do not treat `composition.has("journal")` as membership.

From 0.67.8 the journal organ is the attach on `runtime.event`. `host.event_journal` is that object. Catch-up and redrive see orchestration events (`job.completed`, `resource.changed`). Emitting only on `host.event` does not append. Journal is not a supervised loop.

From 0.67.9 `projections` membership is the structure definition list. Host attach follows `has_capability("projections")`. Composition omit does not hide a listed name. `local.embedded` and `local.worker` omit the organ. Do not treat `composition.has("projections")` as membership.

From 0.67.10 the projections organ is the attach on `runtime.event`. Host query slots are that object. Live reads see orchestration events (`job.completed`, `instance.status_changed`). Emitting only on `host.event` does not update the read models. Projections is not a supervised loop.

From 0.67.11 `compensation` membership is the structure definition list. Recover follows `has_capability("compensation")`. Composition omit does not hide a listed name. `local.embedded` and `local.worker` omit the organ. Do not treat `composition.has("compensation")` as membership.

From 0.67.12 the compensation organ is the attach on `runtime.event`. `host._recovery.compensation` is that object. Undo hooks see orchestration events (`wizard.commit.failed`, `resource.failed`). Emitting only on `host.event` does not run compensation. Compensation is not a supervised loop.

From 0.67.13 `webhook` membership is the structure definition list. Recover follows `has_capability("webhook")`. Composition omit does not hide a listed name. `local.embedded` and `local.worker` omit the organ. Do not treat `composition.has("webhook")` as membership. Settings URLs still refine targets.

From 0.67.14 the webhook organ is the install dispatcher. `host.webhook_dispatcher` is that object. Recover aliases it and refines URLs on it. Empty URLs keep empty targets. Webhook is not a supervised loop. Production outbox drain does not POST.

From 0.67.15 `PalmSettings` has no `enable_compensation` or `enable_webhook_dispatcher`. Membership is DNA. Those env names do not seed.

From 0.67.16 `analytics` membership is the structure definition list. Admission follows `has_capability("analytics")`. Composition omit does not hide a listed name. `local.embedded` and `local.worker` omit the organ. Do not treat `composition.has("analytics")` as membership.

From 0.67.17 the analytics organ is the install object. `host.analytics` is that object. When composition builds `AnalyticsService`, leftover binds it onto that slot. `analytics_enabled` refines enabled on that object. DNA omit drops the host slot — composition.services must not keep a twin. Analytics is not a supervised loop. Host-less `ServerContext` still builds the product service from composition.
