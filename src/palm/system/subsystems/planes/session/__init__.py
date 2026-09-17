"""Session plane — outside subject lifecycle (0.58 Session plane).

**Public door (0.58.3)** — seat + multi-attach + **bind law**:

* :class:`SessionPlaneService` / :func:`bind_session_plane_to_runtime`
* :class:`SessionRecord` / :class:`SessionStatus` / :class:`SessionBind`
* :meth:`SessionPlaneService.bind` / :meth:`~SessionPlaneService.require_open`
* :meth:`SessionPlaneService.attach_instance` / reverse lookup
* :meth:`SessionPlaneService.event_matches` / :meth:`~SessionPlaneService.make_event_filter` (0.58.8)
* :meth:`SessionPlaneService.resolve_continue_instance` (active → waiting → last)
* :attr:`SessionRecord.active_instance_id` / :meth:`SessionPlaneService.set_active_instance` (0.58.10)
* :meth:`SessionPlaneService.owns_instance` / :meth:`~SessionPlaneService.require_owned_instance` (0.58.11 SI-015)
* :meth:`SessionPlaneService.get_metadata` / :meth:`~SessionPlaneService.merge_metadata` (0.58.14)
* :meth:`SessionPlaneService.stamp` / :meth:`~SessionPlaneService.replace`
  (0.69.1 / 0.69.8 — named instance-id key; degenerate allow)
* :func:`require_session_plane`

**Ownership:** one instance → one session (exclusive).  
**Active:** focus inside that attach list only — not a foreign-session pass.  
**Owner gate:** bound system session + continue instance must match attach list.  
**Session metadata:** walk/surface/attribution on the record (not job meta).  
**Product door:** ``BoundSurface`` via ``SessionService`` (0.58.14).  
Docs: ``docs/VISION-0.58.md`` §4.1–4.4 · ADR-027 D9–D14 · SI-015/016.

Store uses :class:`~palm.core.storage.StorageEngine` (like work plane).
Surfaces (host, CLI, …) **bind** before driving work.
Continue/resume remains :mod:`palm.system.subsystems.planes.wait`.
Watches filter events by system session; they do not resume.
"""

from palm.system.subsystems.planes.session.plane import (
    InstanceAlreadyAttachedError,
    InstanceNotOwnedError,
    SessionAttributionError,
    SessionClosedError,
    SessionNotFoundError,
    SessionPlaneError,
    SessionPlaneService,
    bind_session_plane_to_runtime,
    require_session_plane,
)
from palm.system.subsystems.planes.session.store import SessionStore
from palm.system.subsystems.planes.session.types import (
    HOST_SESSION_ID,
    HOST_SESSION_ORIGIN,
    WORK_DRAIN_ORIGIN,
    SessionBind,
    SessionRecord,
    SessionStatus,
    looks_like_system_session_id,
    new_session_id,
    service_session_id,
)

__all__ = [
    "HOST_SESSION_ID",
    "HOST_SESSION_ORIGIN",
    "InstanceAlreadyAttachedError",
    "InstanceNotOwnedError",
    "SessionAttributionError",
    "SessionBind",
    "SessionClosedError",
    "SessionNotFoundError",
    "SessionPlaneError",
    "SessionPlaneService",
    "SessionRecord",
    "SessionStatus",
    "SessionStore",
    "WORK_DRAIN_ORIGIN",
    "bind_session_plane_to_runtime",
    "looks_like_system_session_id",
    "new_session_id",
    "require_session_plane",
    "service_session_id",
]
