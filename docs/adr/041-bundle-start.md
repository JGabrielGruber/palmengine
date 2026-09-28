# ADR-041 — Bundle start: loader, drivers, and plugins

**Status:** Proposed  
**Date:** 2026-09-28  
**Theme:** [VISION-0.72](../vision/VISION-0.72.md) (**open**)  
**Amends:** [ADR-040](040-composition-plugin-membership.md) D2, D4, D7  
**Related:** [ADR-032](032-organism-assembly.md) **Accepted** · [ADR-028](028-system-boot.md) **Accepted** · [ADR-019](019-composition-profiles.md) **Accepted**  
**Map:** [PALM.md](../PALM.md)

José reviewed the desk series and locked the duties below. Homes for drivers and services are on `master` (`b65f2a7a`, `cbfc50ee`). This ADR records **structural decisions only**. It does not claim the loader, the readiness join, or the import cuts have landed. Accept with ADR-040 at 0.72 exit, or later under José's sequence.

---

## Context

1. [ADR-040](040-composition-plugin-membership.md) left the package carrier unpaid and kept reading A: packages install, structure enables.  
2. The kernel still installs by name. `system.plugins.ensure` knows the six family keys. `palm.common.plugins` imports plugins and drivers. `StorageFactory` imports a storage module by name.  
3. [ADR-032](032-organism-assembly.md) keeps the assembly definition as structure law after load. The bundle is a different thing: hard-coded wiring. Changing it starts the process again.  
4. A surface is transport and lives in the bundle that mounts it. A service is a product door several surfaces, and some kits, call. Those doors sat in `src/palm`.  
5. `bundles.standard` is the reference host. It is not the parent a new bundle extends. New bundles adopt this ADR. Standard stays until a bundle covers one of its shapes.

## Decision

### D1 — The bundle calls; the loader and the kernel return

The bundle is the entry. It calls its loader, then the kernel. The loader and the kernel return values. They do not call the bundle.

A different driver set, a different plugin set, or a different profile is a new process. A running kernel does not swap either set.

### D2 — The kernel owns driver slots

The kernel defines **drivers** and **driver requirements** (required / optional). The set of slots is closed. A new slot changes the kernel contract.

| Driver | Requirement |
|---|---|
| Storage | Required |
| Workload runtime | Optional. The minimal bundle binds none. |

The job runner stays kernel-internal. It is not a driver and it is not a plugin.

`start` accepts **bound drivers** and a **structure seed**. It does not accept the bundle, the profile, the plugin set, or provenance. The kernel holds no installer and no install phase. It imports nothing from `drivers`, `plugins`, `bundles`, `services`, or the loader.

**Port** stays the name of an effect or admission interface. A driver is not a port. `WorkloadDriver` in `palm.core.workload.driver` is the graph effect protocol. It is not this slot.

### D3 — Drivers and plugins are different duties

| Duty | What it is | How it grows | Readiness |
|---|---|---|---|
| **Driver** | A slot the kernel defines and the bundle binds before `start` | A new slot changes the kernel | The system |
| **Plugin** | A name in a registry the job path or a surface walks | Another registration | No |
| **Assembly definition** | Organs, places, refuse | The system's definition, from the seed | The system |
| **Service** | A product door the bundle constructs | A module on the shared shelf | No |
| **Surface** | A transport the bundle mounts | Code in that bundle | No |

| Family | Duty | Code home today |
|---|---|---|
| Storage | Driver. Required. | `src/drivers/storages` |
| Workload runtime (`local`, `host`, `neonroot`) | Driver. Optional. | `src/drivers/runners` |
| Pattern, kit, transform, provider | Plugin | `src/plugins` |
| Resource, workload | Run-time attach through a driver or a plugin already bound | Definitions and the place registry |
| Service | Shared shelf. The profile names which doors to construct. | `src/services` |
| Surface mount | Bundle code | `bundles.standard` for the reference host |

A provider is not a driver. A resource is not a plugin. An organ is neither. A service is not a surface.

### D4 — The loader installs both sets, then freezes

The profile names a driver set and a plugin set. The loader installs each set exactly, once. Each set is dependency-closed. The loader adds no member. A driver name in the plugin set, or a plugin name in the driver set, is a typed error. The loader fills driver slots and plugin registries, checks driver requirements, and freezes both. It returns bound drivers and provenance (host facts, both sets, load log) side by side.

Detect returns host facts. A fact never adds a driver, a plugin, a resource, or a workload. The bundle does not choose resources or workloads from host facts.

Release frees the bindings and registry entries this load added. On error, the loader releases its partial install first. Release does not unload a module. A new process is the honest reboot.

The loader is not in the tree yet.

### D5 — The loader is replaceable; the bundle names it

A load contract of types only is owned by no stage. It carries a version. `start` refuses a mismatch. The kernel signature has no plugin set and no provenance.

The bundle names or constructs its loader at the entry. The loader does not call the bundle. One bundle is not required to run unchanged on another loader. The stable surface across hosts is the contract and the kernel.

### D6 — The bundle is hard-coded

The profile names the driver set, the plugin set, the structure seed, the services to construct, the surface mounts, the runtimes to spawn, and the settings that profile supports.

Host checks compare facts to what this profile already requires. A miss is a clean no-go. Nothing is loaded. There is no step that turns detection into another member list.

Close / reopen of the same driver under the same profile is that driver's lifecycle.

Workloads and resources attach on a running system through a driver or a plugin already bound. Shipping a new provider, pattern, kit, or transform is a new process.

### D7 — Two definitions

| Definition | Owner | What it is |
|---|---|---|
| **Assembly definition** | System | Desired structure. Organs, places, refuse. Code: `StructureDefinition`. Enabled from the seed. |
| **Bundle** | Bundle | Hard-coded implementation. The assigned profile names both sets, the seed, the services, and the mounts. |

The profile is not the assembly definition. The system owns the definition body and the readiness judgment.

### D8 — Extending a bundle, and assigning a profile, are bundle questions

Both moves are likely. A Palm implementation may extend a bundle, or assign a profile, including a profile that implementation supplies in place of the bundle's own. The mechanism is not locked. The kernel still sees bound drivers and a structure seed.

Direction, not a deletion list: hard-coded bundles replace the current settings soup as the way a shape is chosen.

`bundles.standard` remains the reference for a full phenotype. A new bundle does not subclass `ApplicationHost` to adopt this ADR.

### D9 — Reading A holds

Both sets **install** (loader). The assembly definition **enables** (kernel). [ADR-040](040-composition-plugin-membership.md) D3 is unchanged.

The assembly definition names neither set. The profile enables no organ. Driver, plugin, organ, place, service, and surface stay different labels.

### D10 — Readiness counts drivers

After `start`, assembly status and admission take the bound drivers into account, with the assembly definition.

A required driver that is missing or unhealthy leaves the organism not ready. Admission fails closed. An empty workload runtime is a ready machine when the definition requires no place.

A missing plugin does not make the organism unready. Work that names it fails when that work is materialized.

Driver checks before `start` answer whether this hard-coded bundle opens here. They do not choose another profile.

The minimal bundle is storage `memory`, an empty plugin set, seed `local.embedded`, no service, and no surface.

This readiness join is not in the tree yet.

### D11 — Services are a shared shelf; surfaces stay in the bundle

Surface code lives in the bundle that mounts it. Service code lives in `src/services`. The profile names which doors to construct and which mounts to build.

`palm` does not import `services`. A service may import `palm`. A service does not import a bundle, a surface, or a plugin. A bundle and a kit may import a service.

One shelf. The profile selects. Doors several hosts already share: `inspect`, `session`, `definitions`, `execution`. A fuller host also names `assist`, `design`, and `analytics`.

`services.definitions` still imports `plugins.patterns.wizard`. That arrow is cut on the wiring pass. A service reaches a plugin through a registry the plugin registered into.

### D12 — Accept at theme exit

Status stays **Proposed** until José exits **0.72** and accepts this ADR with ADR-040, or accepts it later under his sequence.

## Explicit non-decisions

This ADR does **not** decide:

- the mechanism for extending a bundle or assigning a profile (D8)  
- type names beyond the duties above, or the physical home of the loader  
- the order of the remaining code moves  
- packaging and the wheel (`pyproject.toml` still ships `src/palm` only)  
- measure pass. O1–O5 stay **not pass**  
- deleting a named settings type. The direction is D8  

## Consequences

- Target import arrows: `palm` reaches neither `drivers`, `plugins`, `bundles`, nor `services`. `services` reaches neither `plugins` nor `bundles`. A bundle and a kit may reach `services`. A service may reach `palm`.  
- O1 becomes two loader equations, diffed against provenance. The kernel sees neither list.  
- `scripts/guard_system.py` still forbids the old prefixes `palm.services`, `palm.runtimes`, `palm.patterns`, and `palm.app`. It does not yet enforce the arrows above.  

### As-built at filing (not the decision)

| Landed | Still open |
|---|---|
| `src/drivers` holds runners and storages | No loader. `start` does not take bound drivers |
| `src/services` holds the product doors | `palm.common.plugins` still imports plugins and drivers |
| | `StorageFactory` still imports `drivers.storages.*` by name |
| | `services.definitions` still imports the wizard plugin |
| | Readiness does not read drivers |
| | `system.plugins.ensure` is still a kernel phase |

## Alternatives considered

- One kernel-owned package set, read during boot. The kernel would still know package names.  
- Smart `select` from host facts into a member list. The bundle would choose resources. José rejected that.  
- Service code inside `bundles.standard`. Kits and a second bundle would import that host to reach a shared door.  
- Treating every plugin family as a driver. Readiness would treat a missing wizard as an unready organism.

## Links

- Theme: [VISION-0.72](../vision/VISION-0.72.md)  
- Amends: [ADR-040](040-composition-plugin-membership.md)  
- Desk series: `archive/adr-041-rev9/` (history, not law)

## Status

**Proposed.** Homes for drivers and services have moved. The loader, the readiness join, and the import cuts have not.
