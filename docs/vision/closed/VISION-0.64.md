# VISION 0.64 — First capability (`work_drain`)

**Status:** ✅ **Theme closed** (José 2026-08-18) at `0.64.0`. Next: [VISION-0.65](VISION-0.65.md) (**closed**).  
**Map:** [PALM.md](../../PALM.md) · vault [architecture/](../../architecture/README.md) · seed [VISION-ASSEMBLY](../VISION-ASSEMBLY.md)  
**Prior:** [VISION-0.63](VISION-0.63.md) (closed) · [ADR-032](../../adr/032-organism-assembly.md)  
**This theme:** [ADR-033](../../adr/033-one-walker.md) **Accepted** — old wiring dies in the same cut.

**This minor is `work_drain` as the first real capability** — the shape every later organ copies. Not a slice queue. Not host-owned drain. Not a private `if`.

| Law | Meaning |
|-----|---------|
| Structure definition lists the name | Membership |
| Walker loops a table | New organ = name + hand |
| Hand takes **seats** | Supervisor + work plane. No shell bag |
| Plane is system | Attach / install board. Host does not stash or configure it |
| Start ports on the board | `submit` / `able`. Host binds product values at spawn |
| AGENTS §1.1 | A cut does not override this |

Cleanup of `host.work_drain` as owner, coordinator bag scrape, and tests that freeze that past is **in** this theme. Alias-to-keep-green is out.

**Admission and capability (José 2026-08-17).** Admission is the **business-rule face**: may this act run. Its goal is that the business-rule layer does **not** talk to system lower layers (engines, supervisor, structure seat). Capability is the **structure fact**: is this organ here. The face should read the fact. It is not a second membership.

| Step | When | Meaning |
|------|------|---------|
| **1. Contract** | 0.63 (closed) | Map citizen edges. Fail closed. Lift business off lower-layer digs. |
| **2. Work** | **this theme** | Real control: name + hand. Omit means it does not run. |
| **3. New contract** | after copyable | Admission still answers the business question. It sits on capabilities (and ready / refuse), not a wall that pretends to be membership. |
| **4. Dependents** | after 3 | Change who still calls the old face (`able`, façades, surfaces, tests that freeze `may_run_business` as the organ list). [SD-020](../../../TECH-DEBT.md#sd-020) lives here. |

Do not swap 2 and 3. Do not open SD-020 as a mid-theme dump. Ready / refuse stay a short gate — not a fake capability named `ready`.

No slice table. Residual: [TECH-DEBT.md](../../../TECH-DEBT.md) · [structure-materialize-cut.md](../../architecture/appendix/structure-materialize-cut.md).

**Exit:** José stamped **copyable** and **closed** the theme (2026-08-18). The home is name + hand + omit. [VISION-0.65](VISION-0.65.md) is closed.

### Horizons (catch-up · José 2026-08-18)

Themes **classify** the work. They are not theater. If a later cut shows the first organ is still missing, that work is still **0.64**.

| Horizon | Status | What it is |
|---------|--------|------------|
| **0.64** | **closed** (José 2026-08-18) · **copyable** | First organ `work_drain`. Next organ is name + hand. If a later cut shows costume, that work is still this theme's law. |
| **0.65** | [closed](VISION-0.65.md) | Proof the home copies: **outbox**. Name + hand + kill the old walker in the same cut. |
| **Assembly remainder** | [VISION-0.66](VISION-0.66.md) (**closed**) · [VISION-0.67](VISION-0.67.md) (**closed**) | Step 3 paid. Step 4 dependents paid. Costume: [VISION-0.68](VISION-0.68.md) (**closed**). |

**Costume landed (no second organ):** composition does not type `work_drain`; assemble / seed / refuse no longer shovel a capabilities bag; `WORK_DRAIN_SERVICE` is gone. Hand still calls `register_work_drain`.

**Grow with 0.65, do not invent now:** `CapabilitySeats`, `system.background.start` skip strings.

**Leave named:** host then `runtime.stop` (shutdown order); ops `start_plane_running`; journal *consumer* also named `work_drain`.

Dogfood (`analytics`, `neonroot`) and always-on engine (`workloads`) are not the capability queue. `inbound` is old pile — do not copy.

---

## After compact (2026-08-17)

**Commits:** `6e50fd6b` first capability (seats, names, no host drain) · `d1b3c23a` ctx seats, no host listed bag · B1 wire catalog no longer freelances `work_drain`. Master may be ahead of origin. Not pushed.

**Law that landed:** Structure definition lists the name. Walker loops `LOCAL_CAPABILITY_HANDS`. Hand takes `CapabilitySeats`. Assemble fills seats from boot `ctx` + install `work_plane`. Drain start is `system.background.start`. It reads `supervisor.get("work_drain")` (walker effect), not the definition again, not `host._work_drain_listed`. Host schedule ends at ready. The host does not start the loop again. Coordinator, tests, and status read `runtime.work_plane`. Default wire catalog does not register `work_drain`. Composition / flag do not write the name. Omit is enough. No host `start_plane` alias.

**Do not:** invent definition `requires` (the old DNA-requires idea); reuse VitalityRegistry for hands; open a 0.64 slice table; fan shared types across worktrees; start journal/outbox until José opens 0.65.

**Process:** parallel **read** (explore agents). One **writer** at a time. Parent keeps the contract short. `src/palm/AGENTS.md` §1.1 / §1.2.

### Next motion (ordered, not stamps)

| Pile | Job | Notes |
|------|-----|--------|
| **A** | **Landed** — dead costume gone | `allow_background_drain` deleted. Seed twins collapsed. `has_capability` / walker is enough. |
| **B1** | **Landed** — wire catalog does not freelance `work_drain` | Hand is the only register. Unregister-on-unlist stays for reassemble. |
| **B2** | **Landed** — refuse reads definition capabilities | Composition listing the name is not a refuse input. Omit is enough. |
| **B3** | **Landed** — composition / flag do not write `work_drain` | Presets, seed-map row, and the settings/deployment fold are gone. Omit is enough. `refuse:background_drain` is not a live wall. |
| **C** | **Landed** — no host/coordinator `start_plane` alias | Coordinator and status read `runtime.work_plane`. Host schedule ends at ready. Drain start is `system.background.start`. Assemble uses `shell.structure`. No `enable_work_drain_service`. Outbox proof is [VISION-0.65](VISION-0.65.md). Definition `requires` — do not invent. |

A, B1–B3, C landed. Named leftovers paid: assemble uses `shell.structure`; settings/deployment have no `enable_work_drain_service`. Vitality default probes share `attr_resolver` (supervisor, execution, install, structure), `get_system_planes` (hub), and `first_resolver` for process log. Inventory `admission_inventory_snapshot` stays as eyes.

**After this close:** Outbox is [VISION-0.65](VISION-0.65.md) (closed). Admission contract is [VISION-0.66](VISION-0.66.md) (closed). Step 4 dependents are [VISION-0.67](VISION-0.67.md) (**closed**). Costume composted: [VISION-0.68](VISION-0.68.md) (**closed**). Residual [SD-023](../../../TECH-DEBT.md#sd-023).
