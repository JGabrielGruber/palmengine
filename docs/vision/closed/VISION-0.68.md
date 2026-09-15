# VISION 0.68 — The great cleansing

**Status:** ✅ **Theme closed** (José 2026-09-15) at `0.68.0`.  
**ADR:** none (costume compost; no new door)  
**Migration:** [MIGRATION-0.68](../../migrations/MIGRATION-0.68.md)  
**Map:** [PALM.md](../../PALM.md) · seed [VISION-ASSEMBLY](../VISION-ASSEMBLY.md) · prior [VISION-0.67](VISION-0.67.md) (**closed**) · [ADR-036](../../adr/036-require-capability.md) **Accepted**  
**Debt:** [SD-023](../../../TECH-DEBT.md#sd-023) exit residual · [SD-021](../../../TECH-DEBT.md#sd-021) profile/env duals

Teaching name: **the great cleansing**. Law: compost remaining **costume** after assembly dependents. Do not invent a new organ. Do not pay delivery.

**Exit:** José closed the theme (2026-09-15). Floor held: one compost of costume, then 0.68.1–16. Residual duals stay **named** ([SD-023](../../../TECH-DEBT.md#sd-023)). No open minor. Navigator remains a queue seed.

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
- Pattern / Provider `ready()`. Living projections organ. Work drain as WorkIntent drain (not the journal consumer of that name).  
- Two Portal slots for **session** vs **instance**. FastMCP kwargs still named `session_id` (trim living copy; do not rename the field here).  
- Remote Palm-provider HTTP (Palm X→Y). Example-pack *unit* tests that only prove the pack builds.

---

## What 0.68 can still compost (2026-09-15)

Discovery after 0.68.12. Recorded so remaining is not empty by amnesia. **José picked execute 2026-09-15:** **0.68.13–16**. Two-read compost ([VERSIONING](../../VERSIONING.md)): costume, then affected dead code (callers, bags, tests that freeze absence). Do not relocate. Do not invert Navigator. Do not deflate surfaces.

### Empty work / unread dual

| Thing | What it is | Why it still lives | 0.68 motion |
|-------|------------|--------------------|-------------|
| Journal consumer `"work_drain"` + `mark_work_drain_caught_up` | Catch-up that counts journal entries under the organ’s name | Same class as 0.68.11/12. Doctor reports lag. No product caller advances the offset. Drain still uses the WorkIntent store. | ✅ **0.68.13** composted the **consumer** and host lag report. Keep the work-drain organ. Do not wire journal consume into drain. |
| `ApplicationHost.redrive_journal` (+ workplane coordinator twin) | Composition-root method, no product/CLI/MCP caller | Compost tests `hasattr` it green. `EventJournal.redrive` is honest journal machinery. | ✅ **0.68.13** dropped the host facade. Keep the journal method. |
| Unread parking lots | `palm.system.ports` / `planes` / `supervisor` re-export shims; `palm.utils`; `palm.patterns.dag.flow` placeholder; `kits.doctor_section` on `INTENTION_KITS = ()` | Callers already moved (SD-016 said drop when migrated). Same class as 0.68.8. | ✅ **0.68.14** composted unread packages and the unused doctor fragment. Closed chronicles that name old paths stay. |
| Vitality skip stubs | Default registry registers `boot_membership` / `system_log_tail` whose sample is always skip | Tests freeze catalog presence and “not in snapshot.” Same smell as runner `ready()` doctor. | ✅ **0.68.14** composted those two stubs. `monitor_agent` stays a parked later skip. |
| Host query facades | `host.instances` / `jobs` / `wizards` | CLI uses the flat methods. Only a test asserts the facade objects equal the flats. | ✅ **0.68.15** composted the unused facade objects. Keep the flats until a surface theme. |

### Living docs that lie

| Thing | What it is | Why it still lives | 0.68 motion |
|-------|------------|--------------------|-------------|
| README as present | Front door still says theme 0.65 / “No open minor.” `run_server(ServerRuntime())` TypeErrors. One-shot `palm resource *` while argparse has no `resource`. | 0.68.3 class: living docs that promise a door the tree does not have. | ✅ **0.68.16** trimmed to STATUS / real CLI. Do not add a `resource` one-shot. |
| Transform count | README **22**; install tuple **21** (test-pinned); live register has extras; catalog still describes gated `parquet_load`. | Unread dual. Tests freeze the 21. | ✅ **0.68.16** locked **24** (`INSTALLED_TRANSFORMS` = live register = catalog). Do not un-gate parquet (ST-004 paid). |
| MCP L0 continue copy | L0 still teaches `{session_id, flow_id, value}` with `inst-1`. Skill already says `instance_id`. | Living lie of **session** vs **instance**. Field rename is surface deflation. | ✅ **0.68.16** L0 continue uses `instance_id`. FastMCP kwargs unchanged. |

### Optional small duals (José kept named at exit — [SD-023](../../../TECH-DEBT.md#sd-023))

| Thing | Note |
|-------|------|
| MCP profile `experimental` | Same tool-group set as `full`. Name with no experiment. |
| Recovery `_webhook_dispatcher` alias | Second pointer so tests can count two seats. Install organ stays. |
| Host `event_plane_status` / `ops_status` / `control_plane_status` | Triple aliases residual (CS-002). `packaging_status` is the bag. |
| `HttpWebhookDeliverer` as unused default | 0.68.3: do not wire production POST. Second scout if still no product caller. Webhook organ stays. |
| Overlapping `find_spec is None` / `"phase not in"` tests | Affected dead code of **already paid** units. Collapse when touching that file. Not a first execute. |

### Suggested first execute (not sealed)

1. Journal consumer `"work_drain"` + host `redrive_journal` (same family as 0.68.11/12).  
2. Unread parking lots + kits `doctor_section` + vitality skip stubs.  
3. README / L0 living lies.

José picked the four slices. Proof stays: a pin that froze empty work now matches the delete, or names the honest skip.

## Locks (José 2026-08-21)

| # | Lock |
|---|------|
| **1** | **Costume, not a new organ.** Delete empty work. Do not add `require_*`. Do not add a capability name to prove the theme. |
| **2** | **Roles, not a shared drain** (carried from 0.67 lock 5). Do not pay outbox POST as two processes polling one `OutboxStore`. Scale home is [VISION-0.56](../VISION-0.56.md). |
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

- Workload spawn of support / work processes. That is [VISION-0.56](../VISION-0.56.md).  
- DNA phenotype retune (`local.cli` vs `local.embedded` lists) unless José names that cut.  
- Navigator invert: Assist command table, operator-entry auto-start, fake catalog turns, example pack as `main()`. [VISION-NAVIGATOR](../VISION-NAVIGATOR.md).  
- Surface identity: Portal FAB / PWA / pt-BR synonym policy / hello auto-start; MCP fat catalog (SU-003); CLI forest as chatbot (SU-005 / SU-008); walk-handle field rename (SI-002). [VISION-SURFACE-DEFLATION](../VISION-SURFACE-DEFLATION.md). Two slots stay honest packaging.  
- Tiny LLM ([VISION-TINY-LLM](../VISION-TINY-LLM.md)). Tunnels. Grove. `PalmProvider` as submit/wait. Speak-after-place blueprint.  
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
| **0.68.13** | Compost journal consumer `"work_drain"` + host `redrive_journal`. Keep the work-drain organ and `EventJournal.redrive`. ✅ |
| **0.68.14** | Compost unread parking lots + kits `doctor_section` + vitality skip stubs `boot_membership` / `system_log_tail`. `monitor_agent` stays parked. ✅ |
| **0.68.15** | Compost unused `host.instances` / `jobs` / `wizards` facades. Keep the flat methods. ✅ |
| **0.68.16** | Trim README / transform-count / L0 continue copy. Do not add `resource` one-shot. Do not un-gate parquet. Do not rename FastMCP kwargs. ✅ |
| **exit** | José · stamp `0.68.0`. ✅ |

*Delete the empty work. Keep the honest knob.*
