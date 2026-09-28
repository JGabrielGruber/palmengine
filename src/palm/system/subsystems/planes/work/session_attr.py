"""Reactive start session attribution on the system path (0.60.4).

Mirrors product :meth:`~services.session.SessionService.enrich_reactive_start`
using the **session plane** only — no product import (system purity).

Law (0.58.16): inherit system ``session_id`` from the signal, else stable
service session for *origin*. Never mint a random outside ``sess-…``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from palm.system.subsystems.planes.session.types import looks_like_system_session_id


def reactive_origin(flow_id: str | None, payload: Mapping[str, Any] | None) -> str:
    """Stable service origin when no session is inherited."""
    meta = dict(payload or {})
    trigger = str(meta.get("trigger") or "").strip().lower()
    fid = str(flow_id or meta.get("flow_name") or "").strip()
    if trigger == "schedule":
        return f"schedule:{fid}" if fid else "schedule"
    inbound_res = meta.get("inbound_resource")
    if trigger == "inbound" or inbound_res:
        res = str(inbound_res or "inbound").strip() or "inbound"
        return f"inbound:{res}"
    if fid:
        return f"work-drain:{fid}"
    return "work-drain"


def attribute_reactive_start(
    runtime: Any | None,
    flow_id: str | None,
    payload: Mapping[str, Any] | None,
    *,
    origin: str | None = None,
    session_plane: Any | None = None,
) -> dict[str, Any]:
    """Return intent payload with system ``session_id`` for automated start.

    Prefer *session_plane* (CS-008). *runtime* remains for lookup/compat only.
    """
    meta = dict(payload or {})
    origin_s = str(origin or "").strip() or reactive_origin(flow_id, meta)

    inherited = None
    for raw in (
        meta.get("session_id"),
        meta.get("parent_session_id"),
    ):
        if looks_like_system_session_id(raw):
            inherited = str(raw).strip()
            break
    if inherited:
        meta["session_id"] = inherited
        meta["session_attribution"] = "inherit"
        meta.setdefault("session_origin", origin_s)
        return meta

    plane = session_plane
    if plane is None and runtime is not None:
        plane = getattr(runtime, "session_plane", None)
        if plane is None:
            plane = getattr(runtime, "_session_plane", None)
    if plane is None:
        return meta

    try:
        rec = plane.ensure_service_session(origin_s)
        sid = str(getattr(rec, "session_id", "") or "").strip()
        if sid:
            meta["session_id"] = sid
            meta["session_origin"] = origin_s
            meta["session_attribution"] = "service"
    except Exception:
        pass
    return meta


__all__ = ["attribute_reactive_start", "reactive_origin"]
