"""SessionPlaneService — system **session** plane (0.58).

Outside subject on :class:`SessionStore` (:class:`~palm.core.storage.StorageEngine`).

* Lifecycle: open / get / close / list
* Multi-attach (0.58.2): attach/detach instances; reverse index
* **Bind law (0.58.3):** surfaces call :meth:`bind` / :meth:`require_open`
  before driving work — no silent instance-only subject
* **Ownership:** one instance → one owner session (exclusive attach)
* **Active instance (0.58.10):** continue **focus** on the record — only among
  attached ids. Not a pass to drive foreign instances.

Does **not** resume jobs. Continue remains the wait plane.
Law detail: docs/VISION-0.58.md §4.1 · ADR-027 D9–D11.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.system.subsystems.planes.session.store import SessionStore
from palm.system.subsystems.planes.session.types import (
    SessionBind,
    SessionRecord,
    SessionStatus,
    new_session_id,
)
from palm.system.subsystems.planes.session.walk_writes import GUIDANCE_INSTANCE_ID

if TYPE_CHECKING:
    from palm.core.storage import StorageEngine


class SessionPlaneError(RuntimeError):
    """Session plane operation failed."""


class SessionNotFoundError(SessionPlaneError):
    """No session for the given id."""


class SessionClosedError(SessionPlaneError):
    """Session is closed and cannot accept mutations."""


class InstanceAlreadyAttachedError(SessionPlaneError):
    """Instance is already attached to a different session."""


class InstanceNotOwnedError(SessionPlaneError):
    """Bound session does not own the instance (SI-015 owner gate).

    Raised when a surface carries a system ``session_id`` and tries to
    continue/drive an ``instance_id`` that is not on that session's attach
    list. Active focus never authorizes a foreign instance.
    """


class SessionAttributionError(SessionPlaneError):
    """Continue or start lacks required system session attribution (0.58.15).

    Raised under **strict attribution** when the session plane is ready and:

    * **continue** has no bound system session and the instance has no owner, or
    * **start** cannot obtain a system session for the submit body.

    Distinct from :class:`InstanceNotOwnedError` (bound session present but
    foreign instance).
    """


class SessionPlaneService:
    """Session plane: lifecycle + multi-attach + surface bind law.

    Lifecycle:
    * construct with :class:`SessionStore` (or storage engine)
    * :meth:`attach` / :meth:`detach` — optional inspect collaborators
      (instance manager, job resolve, wait plane). Not a full runtime bag.
    * :meth:`open` / :meth:`get` / :meth:`close` / :meth:`list_sessions`
    * :meth:`attach_instance` / :meth:`detach_instance` — multi-attach (0.58.2)
    * :meth:`set_active_instance` / :attr:`SessionRecord.active_instance_id` (0.58.10)
    * :meth:`session_for_instance` — reverse lookup
    * :meth:`owns_instance` / :meth:`require_owned_instance` — SI-015 gate (0.58.11)
    * :meth:`require_continue_attribution` — strict attribution (0.58.15)
    * :meth:`bind` / :meth:`require_open` — surface entry law (0.58.3)
    * :meth:`resolve_continue_instance` — active → waiting → last attached
    """

    def __init__(
        self,
        store: SessionStore | None = None,
        *,
        storage: StorageEngine | None = None,
    ) -> None:
        if store is not None:
            self._store = store
        elif storage is not None:
            self._store = SessionStore(storage)
        else:
            raise TypeError("SessionPlaneService requires store= or storage=")
        self._wired = False
        self._instance_manager: Any | None = None
        self._get_job: Any | None = None
        self._wait_plane: Any | None = None

    @property
    def store(self) -> SessionStore:
        return self._store

    @property
    def is_attached(self) -> bool:
        """True after :meth:`attach` (install path). Store works without it."""
        return self._wired

    def attach(
        self,
        *,
        instance_manager: Any | None = None,
        get_job: Any | None = None,
        wait_plane: Any | None = None,
    ) -> None:
        """Wire optional inspect collaborators. Callers extract them."""
        self._instance_manager = instance_manager
        self._get_job = get_job
        self._wait_plane = wait_plane
        self._wired = True

    def detach(self) -> None:
        """Clear inspect collaborators. Session records stay in StorageEngine."""
        self._instance_manager = None
        self._get_job = None
        self._wait_plane = None
        self._wired = False

    def open(
        self,
        *,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionRecord:
        """Create an OPEN session. Id is generated when omitted."""
        sid = (session_id or "").strip() or new_session_id()
        existing = self._store.get(sid)
        if existing is not None:
            if existing.status == SessionStatus.CLOSED:
                raise SessionPlaneError(f"session {sid!r} exists and is closed")
            return existing
        record = SessionRecord(
            session_id=sid,
            status=SessionStatus.OPEN,
            metadata=dict(metadata or {}),
        )
        return self._store.put(record)

    def bind(
        self,
        session_id: str | None = None,
        *,
        create: bool = True,
        metadata: dict[str, Any] | None = None,
        surface: str | None = None,
    ) -> SessionBind:
        """Surface entry: resolve or create a system session (bind law).

        * No ``session_id`` + ``create=True`` → open a new session.
        * Known open/active id → rebind (touch surface metadata).
        * Unknown id + ``create=True`` → open with that id.
        * Unknown id + ``create=False`` → :class:`SessionNotFoundError`.
        * Closed id → :class:`SessionClosedError` (never silently reopen).

        Returns :class:`SessionBind` proof. Does **not** attach instances
        and does **not** resume jobs.
        """
        meta = dict(metadata or {})
        surf = (surface or "").strip() or None
        if surf:
            meta.setdefault("surface", surf)
            meta["last_surface"] = surf

        sid = (session_id or "").strip() or None
        if sid is None:
            if not create:
                raise SessionPlaneError(
                    "bind requires session_id when create=False (no outside subject)"
                )
            rec = self.open(metadata=meta or None)
            return SessionBind.from_record(rec, created=True, surface=surf)

        existing = self._store.get(sid)
        if existing is None:
            if not create:
                raise SessionNotFoundError(f"session not found: {sid!r}")
            rec = self.open(session_id=sid, metadata=meta or None)
            return SessionBind.from_record(rec, created=True, surface=surf)

        if existing.status == SessionStatus.CLOSED:
            raise SessionClosedError(
                f"session {sid!r} is closed; bind refused (create a new session)"
            )

        touched = False
        if meta:
            for key, value in meta.items():
                if existing.metadata.get(key) != value:
                    existing.metadata[key] = value
                    touched = True
        if touched:
            existing.touch()
            existing = self._store.put(existing)
        return SessionBind.from_record(existing, created=False, surface=surf)

    def ensure_service_session(
        self,
        origin: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> SessionRecord:
        """Open or return a stable **service** session for *origin* (0.58.13).

        Service sessions attribute **automated / internal** start (work drain,
        host housekeeping). They are not outside subjects. Id is deterministic
        from *origin* (``sess-svc-…``). Prefer product
        :meth:`~palm.services.session.SessionService.ensure_service_session`.
        """
        from palm.system.subsystems.planes.session.types import service_session_id

        sid = service_session_id(origin)
        meta = dict(metadata or {})
        meta.setdefault("kind", "service")
        meta.setdefault("origin", str(origin).strip())
        existing = self._store.get(sid)
        if existing is not None:
            if existing.status == SessionStatus.CLOSED:
                raise SessionClosedError(
                    f"service session {sid!r} is closed; refuse reopen"
                )
            # Merge stable origin tags without thrashing.
            touched = False
            for key, value in meta.items():
                if existing.metadata.get(key) != value:
                    existing.metadata[key] = value
                    touched = True
            if touched:
                existing.touch()
                return self._store.put(existing)
            return existing
        return self.open(session_id=sid, metadata=meta)

    def ensure_host_session(
        self,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> SessionRecord:
        """Well-known host service session (``sess-svc-host``)."""
        from palm.system.subsystems.planes.session.types import HOST_SESSION_ORIGIN

        meta = dict(metadata or {})
        meta.setdefault("kind", "service")
        meta.setdefault("origin", HOST_SESSION_ORIGIN)
        return self.ensure_service_session(HOST_SESSION_ORIGIN, metadata=meta)

    def require_open(self, session_id: str) -> SessionRecord:
        """Require an existing non-closed session (continue / inspect paths)."""
        rec = self.require(session_id)
        if rec.status == SessionStatus.CLOSED:
            raise SessionClosedError(f"session {session_id!r} is closed")
        return rec

    def get(self, session_id: str) -> SessionRecord | None:
        return self._store.get(session_id)

    # ── session context metadata (0.58.14) ─────────────────────────────────
    # Walk / surface / attribution facts live here — not on job metadata.
    # Product door: SessionService.get_metadata / merge_metadata.

    def get_metadata(self, session_id: str) -> dict[str, Any]:
        """Return a copy of session-context metadata for *session_id*."""
        rec = self.require(session_id)
        return dict(rec.metadata)

    def merge_metadata(
        self,
        session_id: str,
        metadata: dict[str, Any] | None,
    ) -> SessionRecord:
        """Merge *metadata* into the open session record (session context).

        Does not replace the whole map. Closed sessions raise
        :class:`SessionClosedError`. Empty / None *metadata* is a no-op touch
        skip (returns current record).
        """
        rec = self.require_open(session_id)
        meta = dict(metadata or {})
        if not meta:
            return rec
        touched = False
        for key, value in meta.items():
            if rec.metadata.get(key) != value:
                rec.metadata[key] = value
                touched = True
        if touched:
            rec.touch()
            return self._store.put(rec)
        return rec

    def replace_metadata(
        self,
        session_id: str,
        metadata: dict[str, Any] | None,
    ) -> SessionRecord:
        """Replace session-context metadata entirely (rare; prefer merge).

        Reserved plane facts (attach list, active focus) are **not** in
        metadata — only the free-form context map is replaced.
        """
        rec = self.require_open(session_id)
        rec.metadata = dict(metadata or {})
        rec.touch()
        return self._store.put(rec)

    def stamp_guidance_instance(
        self, session_id: str, instance_id: str
    ) -> SessionRecord:
        """Stamp ``guidance_instance_id`` if absent (0.69.1 walk write).

        Degenerate allow: the session must own *instance_id* (attached).
        Does not change continue focus. Attach does not stamp.
        If the key is already set to a different instance, refuse - use
        :meth:`replace_guidance_instance`.
        """
        iid = (instance_id or "").strip()
        rec = self.require_owned_instance(session_id, iid)
        current = rec.metadata.get(GUIDANCE_INSTANCE_ID)
        if current is None or not str(current).strip():
            return self.merge_metadata(session_id, {GUIDANCE_INSTANCE_ID: iid})
        if str(current).strip() == iid:
            return rec
        raise SessionPlaneError(
            f"session {session_id!r} already has "
            f"{GUIDANCE_INSTANCE_ID}={current!r}; use replace_guidance_instance"
        )

    def replace_guidance_instance(
        self, session_id: str, instance_id: str
    ) -> SessionRecord:
        """Replace ``guidance_instance_id`` (explicit walk write).

        Degenerate allow: the session must own *instance_id* (attached).
        The product kit's definition-id predicate is a later slice.
        """
        iid = (instance_id or "").strip()
        self.require_owned_instance(session_id, iid)
        return self.merge_metadata(session_id, {GUIDANCE_INSTANCE_ID: iid})

    def require(self, session_id: str) -> SessionRecord:
        rec = self._store.get(session_id)
        if rec is None:
            raise SessionNotFoundError(f"session not found: {session_id!r}")
        return rec

    def close(self, session_id: str) -> SessionRecord:
        """Mark session CLOSED. Idempotent if already closed.

        Does not detach instances from the record (history stays).
        Reverse index remains until instances are detached or session deleted.
        """
        rec = self.require(session_id)
        if rec.status == SessionStatus.CLOSED:
            return rec
        rec.status = SessionStatus.CLOSED
        rec.touch()
        return self._store.put(rec)

    def list_sessions(
        self,
        *,
        status: SessionStatus | None = None,
        include_closed: bool = True,
    ) -> list[SessionRecord]:
        return self._store.list(status=status, include_closed=include_closed)

    def attach_instance(self, session_id: str, instance_id: str) -> SessionRecord:
        """Attach an instance to a session (multi-attach; 0..N).

        Idempotent if already on this session (does **not** change active).
        Refuses if another session already owns the instance.
        Promotes OPEN → ACTIVE on first attach.

        **Active focus (0.58.10):** a newly attached instance becomes
        ``active_instance_id`` (new work under the session is the continue
        focus). Re-attach of an already listed id leaves focus alone.
        """
        iid = (instance_id or "").strip()
        if not iid:
            raise SessionPlaneError("instance_id is required")
        rec = self.require(session_id)
        if rec.status == SessionStatus.CLOSED:
            raise SessionClosedError(
                f"session {session_id!r} is closed; cannot attach instances"
            )
        owner = self._store.session_id_for_instance(iid)
        if owner is not None and owner != rec.session_id:
            raise InstanceAlreadyAttachedError(
                f"instance {iid!r} already attached to session {owner!r}"
            )
        if iid in rec.instance_ids:
            # Heal missing active on legacy/corrupt records without steal focus.
            if rec.active_instance_id is None:
                rec.active_instance_id = iid
                rec.touch()
                return self._store.put(rec)
            if (
                rec.active_instance_id is not None
                and rec.active_instance_id not in rec.instance_ids
            ):
                rec.active_instance_id = iid
                rec.touch()
                return self._store.put(rec)
            return rec
        rec.instance_ids.append(iid)
        rec.active_instance_id = iid
        if rec.status == SessionStatus.OPEN:
            rec.status = SessionStatus.ACTIVE
        rec.touch()
        return self._store.put(rec)

    def detach_instance(self, session_id: str, instance_id: str) -> SessionRecord:
        """Remove an instance from a session. Idempotent if not attached.

        Closed sessions may still detach (cleanup). Does not reopen closed.

        If the detached id was active, focus moves to the last remaining
        attached instance, or ``None`` when the list is empty (0.58.10).
        """
        iid = (instance_id or "").strip()
        if not iid:
            raise SessionPlaneError("instance_id is required")
        rec = self.require(session_id)
        if iid not in rec.instance_ids:
            return rec
        rec.instance_ids = [x for x in rec.instance_ids if x != iid]
        if rec.active_instance_id == iid:
            rec.active_instance_id = (
                rec.instance_ids[-1] if rec.instance_ids else None
            )
        elif (
            rec.active_instance_id is not None
            and rec.active_instance_id not in rec.instance_ids
        ):
            rec.active_instance_id = (
                rec.instance_ids[-1] if rec.instance_ids else None
            )
        rec.touch()
        return self._store.put(rec)

    def set_active_instance(self, session_id: str, instance_id: str) -> SessionRecord:
        """Set the plane continue focus to an **already attached** instance (0.58.10).

        Does not attach. Does not resume. Closed sessions refuse.
        """
        iid = (instance_id or "").strip()
        if not iid:
            raise SessionPlaneError("instance_id is required")
        rec = self.require_open(session_id)
        if iid not in rec.instance_ids:
            raise SessionPlaneError(
                f"instance {iid!r} is not attached to session {session_id!r}; "
                "attach first, then set_active_instance"
            )
        if rec.active_instance_id == iid:
            return rec
        rec.active_instance_id = iid
        rec.touch()
        return self._store.put(rec)

    def clear_active_instance(self, session_id: str) -> SessionRecord:
        """Clear continue focus without detaching instances (0.58.10)."""
        rec = self.require_open(session_id)
        if rec.active_instance_id is None:
            return rec
        rec.active_instance_id = None
        rec.touch()
        return self._store.put(rec)

    def list_instances(self, session_id: str) -> list[str]:
        """Return attached instance ids for a session (ordered)."""
        return list(self.require(session_id).instance_ids)

    def active_instance(self, session_id: str) -> str | None:
        """Return the plane continue focus id, or None."""
        rec = self.require(session_id)
        active = rec.active_instance_id
        if active is None:
            return None
        if active not in rec.instance_ids:
            return None
        return str(active)

    def session_for_instance(self, instance_id: str) -> SessionRecord | None:
        """Reverse lookup: session that owns this instance, if any."""
        return self._store.get_by_instance(instance_id)

    def owns_instance(self, session_id: str, instance_id: str) -> bool:
        """True when the session's attach list includes the instance (0.58.11).

        Closed sessions may still "own" history for inspect; continue uses
        :meth:`require_owned_instance` which requires a non-closed session.
        """
        sid = (session_id or "").strip()
        iid = (instance_id or "").strip()
        if not sid or not iid:
            return False
        rec = self._store.get(sid)
        if rec is None:
            return False
        if iid in rec.instance_ids:
            return True
        owner = self._store.session_id_for_instance(iid)
        return owner == sid

    def require_owned_instance(
        self, session_id: str, instance_id: str
    ) -> SessionRecord:
        """Owner gate for continue when a system session is bound (SI-015 / 0.58.11).

        * Session must exist and not be closed.
        * ``instance_id`` must be on that session's attach list.
        * Does **not** set active focus. Does **not** resume.
        * Does **not** authorize foreign instances via ``active_instance_id``.

        Raises:
            SessionNotFoundError: unknown session
            SessionClosedError: closed session
            SessionPlaneError: missing ids
            InstanceNotOwnedError: instance not attached to this session
                (orphan or owned by another session)
        """
        sid = (session_id or "").strip()
        iid = (instance_id or "").strip()
        if not sid:
            raise SessionPlaneError("session_id is required for owner gate")
        if not iid:
            raise SessionPlaneError("instance_id is required for owner gate")
        rec = self.require_open(sid)
        if iid in rec.instance_ids:
            return rec
        owner = self._store.session_id_for_instance(iid)
        if owner is not None and owner != sid:
            raise InstanceNotOwnedError(
                f"instance {iid!r} is owned by session {owner!r}, not {sid!r}"
            )
        raise InstanceNotOwnedError(
            f"instance {iid!r} is not attached to session {sid!r}"
        )

    def require_continue_attribution(
        self,
        instance_id: str,
        session_id: str | None = None,
        *,
        strict: bool = True,
    ) -> str | None:
        """Resolve the system session that may continue *instance_id* (0.58.15).

        **Strict (default):** every continue is attributed.

        * System-shaped ``session_id`` present → :meth:`require_owned_instance`
          and return that id.
        * Missing session → look up owner via reverse index; if found, return
          owner id (plane truth is the bind). If no owner →
          :class:`SessionAttributionError` (bare / orphan refuse).
        * Resolve of continue instance from a session is separate
          (:meth:`resolve_continue_instance`); this method only attributes.

        **Compat (``strict=False``):** only gate when ``session_id`` is present
        (0.58.11 SI-015 behavior). Missing session → return ``None`` (legacy
        bare-instance path).

        Returns the bound system session id, or ``None`` only when not strict
        and no session was provided.
        """
        from palm.system.subsystems.planes.session.types import looks_like_system_session_id

        iid = (instance_id or "").strip()
        if not iid:
            raise SessionPlaneError(
                "instance_id is required for continue attribution"
            )
        sid = (session_id or "").strip() or None
        if looks_like_system_session_id(sid):
            self.require_owned_instance(str(sid), iid)
            return str(sid)

        if not strict:
            return None

        owner = self.session_for_instance(iid)
        if owner is None:
            raise SessionAttributionError(
                f"continue instance {iid!r} has no owner session; "
                "bind a system session_id (0.58.15 strict attribution)"
            )
        # Plane reverse index is bind truth — still require open + attach list.
        self.require_owned_instance(owner.session_id, iid)
        return owner.session_id

    def resolve_continue_instance(self, session_id: str) -> str | None:
        """Pick an instance under the session for continue (0.58.8 + 0.58.10).

        Order (plane truth first):

        1. ``active_instance_id`` when still attached
        2. An attached instance that currently has open waits (newest wait wins)
        3. Last attached instance

        Does **not** resume — only selects the product continue handle.
        """
        rec = self.require_open(session_id)
        if not rec.instance_ids:
            return None
        active = rec.active_instance_id
        if active is not None and str(active) in rec.instance_ids:
            return str(active)
        waiting = self.list_waiting(session_id)
        if waiting:
            for w in reversed(waiting):
                if not isinstance(w, dict):
                    continue
                iid = w.get("instance_id")
                if iid and str(iid) in rec.instance_ids:
                    return str(iid)
        return str(rec.instance_ids[-1])

    def attributed_session_id(
        self,
        *,
        event: Any = None,
        payload: dict[str, Any] | None = None,
        context: Any = None,
    ) -> str | None:
        """Best-effort system session id for an event (0.58.8 watches).

        Order: EventContext.session_id → payload system keys → payload
        session_id when system-shaped → reverse index on instance_id.
        """
        ctx = context
        if event is not None and ctx is None:
            ctx = getattr(event, "context", None)
        pay = payload
        if event is not None and pay is None:
            raw = getattr(event, "payload", None)
            pay = dict(raw) if isinstance(raw, dict) else {}
        pay = pay or {}

        if ctx is not None:
            if hasattr(ctx, "session_id") and ctx.session_id:
                return str(ctx.session_id).strip() or None
            if isinstance(ctx, dict) and ctx.get("session_id"):
                return str(ctx["session_id"]).strip() or None

        # 0.58.9: payload session_id is system subject when system-shaped;
        # instance-shaped → reverse index (legacy product payloads).
        raw_sid = pay.get("session_id")
        if raw_sid is not None and str(raw_sid).strip():
            text = str(raw_sid).strip()
            if text.startswith("sess-"):
                return text
            owner = self.session_for_instance(text)
            if owner is not None:
                return owner.session_id

        for key in ("instance_id", "instance"):
            raw = pay.get(key)
            if raw is not None and str(raw).strip():
                owner = self.session_for_instance(str(raw).strip())
                if owner is not None:
                    return owner.session_id

        if ctx is not None:
            iid = getattr(ctx, "instance_id", None) if not isinstance(ctx, dict) else ctx.get("instance_id")
            if iid:
                owner = self.session_for_instance(str(iid).strip())
                if owner is not None:
                    return owner.session_id
        return None

    def event_matches(
        self,
        session_id: str,
        *,
        event: Any = None,
        payload: dict[str, Any] | None = None,
        context: Any = None,
    ) -> bool:
        """True when the event belongs to this system session (fan-in filter)."""
        sid = (session_id or "").strip()
        if not sid:
            return False
        attributed = self.attributed_session_id(
            event=event, payload=payload, context=context
        )
        if attributed == sid:
            return True
        # Instance on attach list even without reverse hit on attribution
        pay = payload
        if event is not None and pay is None:
            raw = getattr(event, "payload", None)
            pay = dict(raw) if isinstance(raw, dict) else {}
        pay = pay or {}
        rec = self.get(sid)
        if rec is None:
            return False
        attached = set(rec.instance_ids)
        for key in ("instance_id", "instance", "session_id"):
            raw = pay.get(key)
            if raw is not None and str(raw).strip() in attached:
                return True
        if context is not None:
            iid = (
                getattr(context, "instance_id", None)
                if not isinstance(context, dict)
                else context.get("instance_id")
            )
            if iid and str(iid).strip() in attached:
                return True
        return False

    def make_event_filter(self, session_id: str) -> Any:
        """Return a predicate ``(event) -> bool`` for subscribe wrappers / WS."""

        def _filter(event: Any) -> bool:
            return self.event_matches(session_id, event=event)

        return _filter

    def inspect(self, session_id: str) -> dict[str, Any]:
        """Journey view for a session: instances + open waits (0.58.5).

        **Inspect only.** Does not resume, input, or cancel jobs. Continue
        remains the wait plane.
        """
        rec = self.require(session_id)
        instances: list[dict[str, Any]] = []
        waiting: list[dict[str, Any]] = []
        for iid in rec.instance_ids:
            row = self._instance_inspect_row(iid, session_id=rec.session_id)
            instances.append(row)
            for w in row.get("waiting_on") or []:
                if isinstance(w, dict):
                    waiting.append(
                        {
                            **w,
                            "instance_id": iid,
                            "job_id": row.get("job_id"),
                            "session_id": rec.session_id,
                        }
                    )
        active = rec.active_instance_id
        if active is not None and active not in rec.instance_ids:
            active = None
        return {
            "kind": "session_inspect",
            "session_id": rec.session_id,
            "status": rec.status.value,
            "metadata": dict(rec.metadata),
            "created_at": rec.created_at,
            "updated_at": rec.updated_at,
            "instance_ids": list(rec.instance_ids),
            "active_instance_id": active,
            "instances": instances,
            "waiting_on": waiting,
            "counts": {
                "instances": len(rec.instance_ids),
                "open_waits": len(waiting),
            },
            "note": "inspect only; continue via wait plane (not session resume)",
        }

    def list_waiting(self, session_id: str) -> list[dict[str, Any]]:
        """Open wait interests across all instances attached to the session."""
        return list(self.inspect(session_id).get("waiting_on") or [])

    def _instance_inspect_row(
        self, instance_id: str, *, session_id: str
    ) -> dict[str, Any]:
        row: dict[str, Any] = {
            "instance_id": instance_id,
            "session_id": session_id,
        }
        manager = self._instance_manager
        if manager is None:
            return row
        inst = None
        try:
            inst = manager.get(instance_id)
        except Exception:
            inst = None
        if inst is None:
            row["status"] = "unknown"
            return row
        row["status"] = getattr(inst, "status", None)
        row["job_id"] = getattr(inst, "job_id", None)
        row["flow_id"] = getattr(inst, "flow_id", None) or getattr(
            inst, "flow_name", None
        )
        row["pattern"] = getattr(inst, "pattern", None)
        resolved = None
        if hasattr(inst, "resolved_session_id"):
            try:
                resolved = inst.resolved_session_id()
            except Exception:
                resolved = getattr(inst, "session_id", None)
        else:
            resolved = getattr(inst, "session_id", None)
        if resolved:
            row["session_id"] = resolved
        job = self._resolve_job(getattr(inst, "job_id", None))
        waits: list[dict[str, Any]] = []
        if job is not None:
            waits = self._waiting_on_for_job(job)
        if not waits:
            # Fallback: interests on durable instance state (resume-shaped).
            waits = self._waiting_on_from_instance(inst)
        if waits:
            row["waiting_on"] = waits
            try:
                from palm.system.subsystems.planes.wait.present import summarize_waiting_on

                summary = summarize_waiting_on(waits)
            except Exception:
                summary = None
            if summary:
                row["waiting_summary"] = summary
        return row

    def _waiting_on_from_instance(self, inst: Any) -> list[dict[str, Any]]:
        try:
            from palm.system.subsystems.planes.wait.present import waiting_on_from_state
            from palm.common.persistence.state_snapshot import state_from_snapshot

            snap = getattr(inst, "state_snapshot", None)
            if not snap:
                return []
            state = state_from_snapshot(snap)
            return list(waiting_on_from_state(state) or [])
        except Exception:
            return []

    def _resolve_job(self, job_id: str | None) -> Any | None:
        if not job_id:
            return None
        get_job = self._get_job
        if not callable(get_job):
            return None
        try:
            return get_job(str(job_id))
        except Exception:
            return None

    def _waiting_on_for_job(self, job: Any) -> list[dict[str, Any]]:
        wait_plane = self._wait_plane
        if wait_plane is not None and hasattr(wait_plane, "waiting_on_for_job"):
            try:
                return list(wait_plane.waiting_on_for_job(job) or [])
            except Exception:
                pass
        try:
            from palm.system.subsystems.planes.wait.present import waiting_on_from_job

            return list(waiting_on_from_job(job) or [])
        except Exception:
            return []

    def doctor_snapshot(self) -> dict[str, Any]:
        """Small inspect payload for doctor / system diagnostics."""
        open_n = len(self._store.list(status=SessionStatus.OPEN, include_closed=False))
        active_n = len(
            self._store.list(status=SessionStatus.ACTIVE, include_closed=False)
        )
        closed_n = len(self._store.list(status=SessionStatus.CLOSED))
        attached_instances = 0
        for rec in self._store.list(include_closed=True):
            attached_instances += len(rec.instance_ids)
        backend = getattr(self._store.storage, "backend_name", None)
        return {
            "plane": "session",
            "session_plane_attached": self.is_attached,
            "verbs": [
                "bind",
                "require_open",
                "open",
                "get",
                "close",
                "list",
                "attach_instance",
                "detach_instance",
                "set_active_instance",
                "clear_active_instance",
                "active_instance",
                "session_for_instance",
                "owns_instance",
                "require_owned_instance",
                "require_continue_attribution",
                "resolve_continue_instance",
                "inspect",
                "list_waiting",
                "event_matches",
                "attributed_session_id",
                "make_event_filter",
                "stamp_guidance_instance",
                "replace_guidance_instance",
            ],
            "store": "storage_engine",
            "storage_backend": backend,
            "multi_attach": True,
            "active_instance": True,
            "owner_gate": True,
            "strict_attribution": True,
            "bind_law": True,
            "event_filter": True,
            "counts": {
                "open": open_n,
                "active": active_n,
                "closed": closed_n,
                "total": len(self._store),
                "attached_instances": attached_instances,
            },
        }


def bind_session_plane(
    install: Any,
    planes: Any,
    *,
    ensure_host: bool = True,
    reuse_existing: bool = True,
) -> SessionPlaneService:
    """
    Install session on the *planes* subsystem using *install* interface.

    Seat-first DI — no system instance bag. Always ensures the well-known
    **host** service session when *ensure_host* is true (0.58.13).
    """
    return planes.install_session(
        install,
        ensure_host=ensure_host,
        reuse_existing=reuse_existing,
    )


def bind_session_plane_to_runtime(runtime: Any) -> SessionPlaneService:
    """Shell bridge: resolve install + planes seats, then :func:`bind_session_plane`."""
    from palm.system.subsystems.planes.hub import SystemPlanes
    from palm.system.subsystems.planes.install_access import require_system_install

    board = require_system_install(runtime)
    planes = SystemPlanes.ensure_on(runtime)
    return bind_session_plane(board, planes)


__all__ = [
    "InstanceAlreadyAttachedError",
    "InstanceNotOwnedError",
    "SessionAttributionError",
    "SessionClosedError",
    "SessionNotFoundError",
    "SessionPlaneError",
    "SessionPlaneService",
    "bind_session_plane",
    "bind_session_plane_to_runtime",
    "require_session_plane",
]


def require_session_plane(runtime: Any) -> SessionPlaneService:
    """Return the runtime's session plane or raise (bind law helper)."""
    plane = getattr(runtime, "session_plane", None)
    if isinstance(plane, SessionPlaneService):
        return plane
    raise SessionPlaneError(
        "runtime has no session plane; start the system instance first"
    )
