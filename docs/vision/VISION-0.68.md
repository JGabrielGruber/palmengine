# VISION 0.68 — The great cleansing

**Status:** 📗 **Theme open** (José 2026-08-21). Plan `0.68.0`. Package stamp stays `0.67.0` until exit.  
**ADR:** none (costume compost; no new door)  
**Migration:** [MIGRATION-0.68](../migrations/MIGRATION-0.68.md)  
**Map:** [PALM.md](../PALM.md) · seed [VISION-ASSEMBLY](VISION-ASSEMBLY.md) · prior [VISION-0.67](closed/VISION-0.67.md) (**closed**) · [ADR-036](../adr/036-require-capability.md) **Accepted**  
**Debt:** [SD-021](../../TECH-DEBT.md#sd-021) residual packaging duals · empty boot phases after leftover

Teaching name: **the great cleansing**. Law: compost remaining **costume** after assembly dependents. Do not invent a new organ. Do not pay delivery.

---

## Goal

0.67 paid the organ door and the remaining composition kings. Leftover made one object per organ. What still sits is **empty work**, **start-option duals**, and **living docs that lie**.

Delete costume. Keep honest packaging. Leave closed chronicles as history.

## Floor

- Name the remaining pile in this file (this slice).  
- First execute (`0.68.1`) composts **one** costume unit that does no work: empty boot phase, unread dual, or a living lie.  
- Proof: a test or inventory pin that used to freeze empty work now matches the deleted costume, or names the honest skip.  
- Do not add a capability. Do not add a require. Do not POST.

**Floor function:** one compost of costume. Not a new membership name.

## Named remaining (José 2026-08-21)

These still live after 0.67.17. They are **not** unpaid leftover organs.

| Thing | What it is | Why it still lives | 0.68 motion |
|-------|------------|--------------------|-------------|
| `host.projections.attach` / `_attach_projections` | Boot-schedule step whose body is empty | Leftover already attached on the runtime bus. 0.59 dogfood pinned this **phase id**. | ✅ **0.68.1** composted. Inventory pins retuned onto admission. Closed 0.59 chronicle stays. |
| Bare `enable_event_outbox` | Start option still **read** | Host spawn **wrote** it from DNA. `system.outbox.wire` skipped on `enable_event_outbox_off`. | ✅ **0.68.4** composted. Wire skips `capability_off:outbox` when DNA omits. Flag gone. Keep the skip. |
| Runner `ready()` doctor callbacks | Side-effect boot hook | `HostRunnerApp.ready()` registered `DoctorContributor` side-effects. `WorkloadEngine` already samples runner seats. Vitality does not. | ✅ **0.68.2** composted. Anatomy doctor uses `workloads` from the engine. No Vitality runner probe. |
| Living docs that promise POST | Lie | Production never HTTP POSTs. `on_before_publish` is a test hook. | ✅ **0.68.3** trimmed. Living tables no longer promise POST. Do not wire production POST. Closed 0.10 chronicle stays. ✅ **0.68.10** composted unused `host.webhook.delivered` / `failed` names. |
| Twin seats / inventory ids that pin empty work | Costume after leftover | `LocalRunnerApp.ready()` was an empty override after 0.68.2. Same class as unread `enable_compensation` (paid 0.67.15). | ✅ **0.68.5** composted the Local override. ✅ **0.68.6** composted the runner `ready()` call. ✅ **0.68.7** composted the write-only `RunnerApp` bag. ✅ **0.68.9** composted the Pattern MCP second `ready()` call. Pattern/Provider `ready()` stays. |
| Empty `palm.common.runtimes` parking lot | Package with `__all__ = []` after 0.68.2 | Doctor-contributor registry died; tests imported the package only to freeze absence. | ✅ **0.68.8** composted. Living runtime is `palm.system.runtime`. Closed 0.48 / 0.57 chronicles stay. |
| Unused webhook journal facade | Host `drain_journal_webhooks` + `consume_for_webhooks` + doctor key `"webhooks"` | Catch-up that counts journal entries. No product caller. No POST. | ✅ **0.68.11** composted. Do not wire `dispatch`. Closed 0.40 chronicle stays. |
| Unused projection journal facade | Host `drain_journal_projections` + `consume_for_projections` + doctor key `"projections"` | Catch-up that counts journal entries. No product caller. No rebuild. | ✅ **0.68.12** composted. Living projections organ stays. `work_drain` stays. Do not wire this drain into rebuild. Closed 0.40 chronicle stays. |
| `enable_state_snapshot` | **Read** packaging | Installs `StateSnapshotHook`. CLI and settings pass it. Not a membership seed. | **Keep** as packaging unless José later says it is a membership lie. |

Honest packaging that **stays** unless José includes it:

- `analytics_enabled` / `webhook_urls` refine the install organ.  
- Host-less `ServerContext` is a second composition root (ADR-019). Do not dissolve it to fake one leftover path.  
- DNA lists on `local.cli` vs `local.embedded` — José has not locked phenotypes.

## Locks (José 2026-08-21)

| # | Lock |
|---|------|
| **1** | **Costume, not a new organ.** Delete empty work. Do not add `require_*`. Do not add a capability name to prove the theme. |
| **2** | **Roles, not a shared drain** (carried from 0.67 lock 5). Do not pay outbox POST as two processes polling one `OutboxStore`. Scale home is [VISION-0.56](VISION-0.56.md). |
| **3** | **Closed chronicles stay history.** Retune tests that pin empty phases. Do not rewrite 0.59 as if the phase never existed. |
| **4** | Remaining compost stays **in 0.68**. Do not open 0.69 for this pile. |
| **5** | **Read flags are not unread flags.** Compost `enable_event_outbox` only with a DNA-shaped skip. Do not delete `enable_state_snapshot` because it looks like a flag. |

Lock 2 is the fork from leftover option B as “whoever drains the shared store POSTs.” Lock 5 is the fork from treating every `enable_*` as 0.67.15 compost.

## Forbidden always

- Pay webhook delivery as two drainers on one `OutboxStore` (flock / first-ACK-wins).  
- HTTP POST from production recover.  
- Dissolve `ServerContext` to force host leftover onto MCP.  
- Definition `requires`.  
- A fake capability named `ready`.  
- Restamp ADR-036 residual bullets as if leftover slices were kings.

## Not this theme

- Workload spawn of support / work processes. That is [VISION-0.56](VISION-0.56.md).  
- DNA phenotype retune (`local.cli` vs `local.embedded` lists) unless José names that cut.  
- Navigator. Tiny LLM ([VISION-TINY-LLM](VISION-TINY-LLM.md)). Tunnels. Grove. Surface compost ([VISION-SURFACE-DEFLATION](VISION-SURFACE-DEFLATION.md) is a different pile).  
- Engine as walker. Two doors stay as 0.67 law.

## Guide slices (not a sealed contract)

| Slice | Intent |
|-------|--------|
| **0.68.0** | Plan + named remaining. ✅ |
| **0.68.1** | Compost empty `host.projections.attach`. ✅ |
| **0.68.2** | Compost runner `ready()` doctor register. ✅ |
| **0.68.3** | Trim living POST lies. ✅ |
| **0.68.4** | Compost bare `enable_event_outbox` to DNA skip. ✅ |
| **0.68.5** | Compost empty `LocalRunnerApp.ready()`. ✅ |
| **0.68.6** | Compost the runner `ready()` call. ✅ |
| **0.68.7** | Compost the write-only `RunnerApp` bag. ✅ |
| **0.68.8** | Compost empty `palm.common.runtimes`. ✅ |
| **0.68.9** | Compost the Pattern MCP second `ready()` call. ✅ |
| **0.68.10** | Compost unused `host.webhook.delivered` / `failed`. ✅ |
| **0.68.11** | Compost unused webhook journal facade. ✅ |
| **0.68.12** | Compost unused projection journal facade. ✅ |
| **0.68.13+** | Compost units José includes. |
| **exit** | José · stamp `0.68.0`. |

*Delete the empty work. Keep the honest knob.*
