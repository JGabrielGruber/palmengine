"""
Host schedule handlers — start law for ApplicationHost (0.59.4 / 0.59.5).

**Ownership:** host boot owns *when* and *in what order* the composition root
comes up. Handlers here are the rules. Collaborators (kernel, spawner, CQRS
wire, recovery, workplane) are tools — they do not own boot order.

**Membership:** ``CompositionProfile`` still switches services, surfaces, and
capabilities other than ``work_drain``, ``outbox``, ``journal``, and
``projections``. Those organs follow definition ``capabilities``. Drain/outbox
loops start on the system schedule (``system.background.start``) after assemble.
Journal and projections are attach, not loops — the host slot reads the seated
organ. The host does not start them again.

**Break / harvest:** mid-theme breakage is expected. BootMode and PhaseSkip
are the switches. Do not restore import-order magic.

**Dependency direction:**

- ``ApplicationHost.start`` → walker + these handlers
- handlers → host collaborators (methods / coordinators) as a bag of tools
- collaborators must not re-enter host boot tables

Observation: SystemLog only (handlers do not wrap ``slog.phase`` themselves).
"""

from __future__ import annotations

from typing import Any

from palm.app.bootstrap import runtime_start_options
from palm.app.host.boot.system_log_phase import make_host_system_log_handler
from palm.app.host.events import HostEventType
from palm.app.host.workers import WorkerCoordinator
from palm.system.boot.context import BootContext
from palm.system.boot.skip import PhaseSkip
from palm.system.boot.walker import PhaseHandler
from palm.system.log import get_system_log


def build_host_handlers(
    host: Any,
    options: dict[str, Any],
) -> dict[str, PhaseHandler]:
    """Build the full host schedule handler map for one ``start()`` call.

    ``host`` is the ApplicationHost shell — structure target, not schedule owner.
    """

    def kernel_bootstrap(_ctx: BootContext) -> None:
        host._app.bootstrap(host.composition)

    def host_event(_ctx: BootContext) -> None:
        host._event.initialize()
        host._event_recorder.attach(host._event)

    def workers_note(_ctx: BootContext) -> None:
        host._worker_coordinator = WorkerCoordinator(host.profile, host._event)

    def system_spawn(_ctx: BootContext) -> None:
        merged = runtime_start_options(host.settings, **options)
        # 0.72.3 — system.plugins.ensure installs this set. The kernel call
        # above already installed the same names.
        merged["composition_packages"] = host.composition.package_names()
        # 0.63.5 / 0.63.13 — seed structure definition + membership for refuse.
        # Caller definition override still wins; membership always seeds so dual shapes
        # fail closed under refuse (env/composition cannot hide from admission).
        if not merged.get("structure_skip"):
            from palm.system.structure.seed import seed_structure_options_from_host

            seed = seed_structure_options_from_host(host)
            # Surface membership always from host composition unless caller set it.
            if "structure_surfaces" not in options:
                merged["structure_surfaces"] = seed["structure_surfaces"]
            # Structure definition: runtime options / explicit definition win; else seed (incl. env).
            if "structure_definition" not in options and "structure_definition_id" not in options:
                merged["structure_definition_id"] = seed["structure_definition_id"]
                merged["structure_definition"] = seed["structure_definition"]
        # Start ports on the install board from spawn — able is drain-shaped
        # and false until host.ready. Wait uses a ready-only sibling.
        # System background start may start drain; the loop idles until able.
        if "install_submit" not in options:
            submit, able, admission_able = host._workplane.start_ports()
            merged["install_submit"] = submit
            merged["install_able"] = able
            merged["install_admission_able"] = admission_able
        host._spawner.spawn_runtimes(merged)

    def definitions_load(_ctx: BootContext) -> None:
        host._app.load_definitions()

    def product_wire(_ctx: BootContext) -> None:
        host._wire_cqrs()
        # Membership truth narrative (0.59.5) — what services the schedule built.
        built = [
            name for name in host.composition.services if getattr(host, name, None) is not None
        ]
        get_system_log().system(
            "product.wire",
            "product services wired from composition",
            schedule="host",
            services=",".join(built) or "(none)",
            capabilities=",".join(sorted(host.composition.capabilities)) or "(none)",
        )

    def surfaces_mount(_ctx: BootContext) -> None:
        # Membership: deployment selects *where* HTTP runs; composition.surfaces
        # is *what* mounts. Both must be on — no silent full surface set.
        if not host.profile.server:
            raise PhaseSkip("deployment.server_off")
        if not host.composition.surfaces:
            raise PhaseSkip("composition_off:surfaces")
        host._start_server_surface()
        get_system_log().system(
            "surfaces.mount",
            "server surfaces mount",
            schedule="host",
            surfaces=",".join(host.composition.surfaces),
        )

    def recover(_ctx: BootContext) -> None:
        if host.boot_mode is not None and not host.boot_mode.recover_on_start:
            raise PhaseSkip("mode_recover_off")
        host._recovery.recover()

    def ready(ctx: BootContext) -> None:
        roles = sorted(host.profile.roles)
        host._event.emit(
            HostEventType.STARTED,
            roles=roles,
            primary=host._app.primary_name,
        )
        host._started = True
        get_system_log().info(
            "ready",
            "host ready",
            schedule="host",
            mode=ctx.mode,
            primary=host._app.primary_name,
            roles=",".join(roles) or "(none)",
        )

    return {
        "host.system_log": make_host_system_log_handler(host.boot_mode),
        "host.kernel.bootstrap": kernel_bootstrap,
        "host.event": host_event,
        "host.workers.note": workers_note,
        "host.system.spawn": system_spawn,
        "host.definitions.load": definitions_load,
        "host.product.wire": product_wire,
        "host.surfaces.mount": surfaces_mount,
        "host.recover": recover,
        "host.ready": ready,
    }


__all__ = ["build_host_handlers"]
