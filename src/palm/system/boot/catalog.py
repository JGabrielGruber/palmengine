"""
System phase definition catalog — membership of system start (0.61).

**Order** lives on :data:`~palm.system.boot.phases.SYSTEM_PHASES`.
**How** lives on each subject's phase module (co-located):

| Phase id | Home |
|----------|------|
| system.log.ready | ``palm.system.log.phase_ready`` |
| system.engines.init | ``palm.system.runtime.phase_engines`` |
| system.storage.select | ``palm.system.runtime.phase_storage`` |
| system.outbox.wire | ``palm.system.runtime.phase_outbox`` |
| system.hooks.install | ``palm.system.runtime.phase_hooks`` |
| system.orchestration.start | ``palm.system.runtime.phase_orchestration_start`` |
| system.install.bind | ``palm.system.interfaces.phase_install_bind`` |
| system.planes.attach | ``palm.system.subsystems.planes.phase_attach`` |
| system.supervisor.wire | ``palm.system.subsystems.supervisor.phase_wire`` |
| system.bind | ``palm.system.runtime.phase_provider_bind`` |
| system.ready | ``palm.system.runtime.phase_ready`` |
| system.structure.assemble | ``palm.system.structure.phase_assemble`` |
| system.background.start | ``palm.system.subsystems.supervisor.phase_background`` |

Boot only **imports** definitions and walks them. New step = subject module
+ entry here + :class:`~palm.system.boot.phases.PhaseSpec` row.
"""

from __future__ import annotations

from palm.system.boot.definition import PhaseDefinition
from palm.system.interfaces.phase_install_bind import DEFINITION as _install_bind
from palm.system.log.phase_ready import DEFINITION as _log_ready
from palm.system.runtime.phase_engines import DEFINITION as _engines
from palm.system.runtime.phase_hooks import DEFINITION as _hooks
from palm.system.runtime.phase_orchestration_start import (
    DEFINITION as _orchestration_start,
)
from palm.system.runtime.phase_outbox import DEFINITION as _outbox
from palm.system.runtime.phase_provider_bind import DEFINITION as _bind
from palm.system.runtime.phase_ready import DEFINITION as _ready
from palm.system.runtime.phase_storage import DEFINITION as _storage
from palm.system.structure.phase_assemble import DEFINITION as _structure_assemble
from palm.system.subsystems.planes.phase_attach import DEFINITION as _planes_attach
from palm.system.subsystems.supervisor.phase_background import (
    DEFINITION as _background,
)
from palm.system.subsystems.supervisor.phase_wire import DEFINITION as _supervisor_wire

# Membership of the system start catalog (not walk order).
DEFAULT_SYSTEM_PHASE_DEFINITIONS: tuple[PhaseDefinition, ...] = (
    _log_ready,
    _engines,
    _storage,
    _outbox,
    _hooks,
    _orchestration_start,
    _install_bind,
    _planes_attach,
    _supervisor_wire,
    _bind,
    _ready,
    _structure_assemble,
    _background,
)

_BY_ID: dict[str, PhaseDefinition] = {d.id: d for d in DEFAULT_SYSTEM_PHASE_DEFINITIONS}


def system_phase_definition(phase_id: str) -> PhaseDefinition | None:
    return _BY_ID.get(phase_id)


def system_phase_definitions() -> tuple[PhaseDefinition, ...]:
    return DEFAULT_SYSTEM_PHASE_DEFINITIONS


def definitions_for_phases(
    phase_ids: tuple[str, ...] | list[str],
) -> list[PhaseDefinition]:
    """Resolve definitions in *phase_ids* order; skip unknown ids."""
    out: list[PhaseDefinition] = []
    for pid in phase_ids:
        defn = _BY_ID.get(pid)
        if defn is not None:
            out.append(defn)
    return out


__all__ = [
    "DEFAULT_SYSTEM_PHASE_DEFINITIONS",
    "definitions_for_phases",
    "system_phase_definition",
    "system_phase_definitions",
]
