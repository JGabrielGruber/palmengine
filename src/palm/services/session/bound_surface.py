"""BoundSurface — session-owned surface context (0.58.14).

Surfaces hold **one** :class:`BoundSurface` as truth for who is walking
and which instance is the continue focus. They do not invent dual slots
(``active_system_*`` + ``active_assist_*`` + private plane access).

* ``session_id`` — system subject (``sess-…`` | ``sess-svc-…``)
* ``instance_id`` — continue focus under that session (or None)
* ``kind`` — ``outside`` | ``service`` | ``host``
* ``origin`` — optional attribution (mcp | cli | work-drain:{flow} | …)
* ``metadata`` — **session** context snapshot (walk / surface / attribution),
  not job blackboard

Plane remains law for attach list and ownership. This type is the product
shape SessionService returns so edges share one handle.

See VISION-0.58 §4.3–4.4 · ADR-027 D13–D14 · SI-016.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from palm.system.subsystems.planes.session.types import (
    HOST_SESSION_ID,
    HOST_SESSION_ORIGIN,
    looks_like_system_session_id,
)

# Session-context keys that describe the subject (not job-run facts).
SESSION_CONTEXT_KEYS = frozenset(
    {
        "kind",
        "origin",
        "surface",
        "last_surface",
        "session_origin",
        "client",
        "labels",
        "prefs",
        "walk",
    }
)

BoundSurfaceKind = str  # outside | service | host


def derive_session_kind(
    session_id: str,
    metadata: Mapping[str, Any] | None = None,
) -> str:
    """Derive BoundSurface kind from id + session metadata."""
    meta = dict(metadata or {})
    sid = str(session_id or "").strip()
    raw = meta.get("kind")
    if sid == HOST_SESSION_ID or str(meta.get("origin") or "") == HOST_SESSION_ORIGIN:
        return "host"
    if raw == "host":
        return "host"
    if sid.startswith("sess-svc-") or raw == "service":
        return "service"
    if raw == "outside":
        return "outside"
    return "outside"


def derive_session_origin(
    session_id: str,
    metadata: Mapping[str, Any] | None = None,
) -> str | None:
    """Prefer explicit origin / session_origin; host is well-known."""
    meta = dict(metadata or {})
    for key in ("origin", "session_origin"):
        val = meta.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    if str(session_id or "").strip() == HOST_SESSION_ID:
        return HOST_SESSION_ORIGIN
    return None


@dataclass(frozen=True)
class BoundSurface:
    """Session-owned surface context handle (0.58.14).

    Immutable snapshot for transport and product edges. Mutations go through
    :class:`~palm.services.session.SessionService` (bind / merge metadata /
    set active), then rebuild via :meth:`SessionService.surface_from_session`.
    """

    session_id: str
    instance_id: str | None = None
    kind: str = "outside"
    origin: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        # Defensive copy so callers cannot mutate our frozen snapshot via
        # the dict reference they passed in.
        object.__setattr__(self, "metadata", dict(self.metadata or {}))
        sid = str(self.session_id or "").strip()
        if not sid:
            raise ValueError("BoundSurface.session_id must be non-empty")
        if not looks_like_system_session_id(sid):
            raise ValueError(
                f"BoundSurface.session_id must be system-shaped (sess-…), got {sid!r}"
            )
        object.__setattr__(self, "session_id", sid)
        iid = self.instance_id
        if iid is not None:
            text = str(iid).strip()
            object.__setattr__(self, "instance_id", text or None)
        k = str(self.kind or "outside").strip().lower() or "outside"
        if k not in ("outside", "service", "host"):
            k = derive_session_kind(sid, self.metadata)
        object.__setattr__(self, "kind", k)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "kind": "bound_surface",
            "session_id": self.session_id,
            "instance_id": self.instance_id,
            "session_kind": self.kind,
            "origin": self.origin,
            "metadata": dict(self.metadata),
        }
        return out

    def with_instance(self, instance_id: str | None) -> BoundSurface:
        """Return a copy with a different continue focus (local only)."""
        return BoundSurface(
            session_id=self.session_id,
            instance_id=instance_id,
            kind=self.kind,
            origin=self.origin,
            metadata=dict(self.metadata),
        )

    def with_metadata(self, metadata: Mapping[str, Any]) -> BoundSurface:
        """Return a copy with replaced metadata snapshot (local only)."""
        return BoundSurface(
            session_id=self.session_id,
            instance_id=self.instance_id,
            kind=self.kind,
            origin=self.origin,
            metadata=dict(metadata),
        )

    @classmethod
    def from_record(
        cls,
        record: Any,
        *,
        instance_id: str | None = None,
    ) -> BoundSurface:
        """Build from a :class:`~palm.system.subsystems.planes.session.SessionRecord`."""
        sid = str(record.session_id)
        meta = dict(getattr(record, "metadata", None) or {})
        iid = instance_id
        if iid is None:
            active = getattr(record, "active_instance_id", None)
            if active is not None and str(active).strip():
                iid = str(active).strip()
        return cls(
            session_id=sid,
            instance_id=iid,
            kind=derive_session_kind(sid, meta),
            origin=derive_session_origin(sid, meta),
            metadata=meta,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> BoundSurface:
        """Rebuild from :meth:`to_dict` or a params-like mapping."""
        sid = data.get("session_id")
        if not looks_like_system_session_id(sid):
            raise ValueError(
                f"BoundSurface.from_dict requires system session_id, got {sid!r}"
            )
        meta = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
        sk = data.get("session_kind") or data.get("surface_kind") or meta.get("kind")
        origin = data.get("origin")
        if origin is None:
            origin = derive_session_origin(str(sid), meta)
        kind = str(sk) if sk else derive_session_kind(str(sid), meta)
        return cls(
            session_id=str(sid),
            instance_id=data.get("instance_id"),
            kind=kind,
            origin=str(origin).strip() if origin is not None else None,
            metadata=dict(meta),
        )


__all__ = [
    "SESSION_CONTEXT_KEYS",
    "BoundSurface",
    "BoundSurfaceKind",
    "derive_session_kind",
    "derive_session_origin",
]
