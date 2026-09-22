"""WebSocket control-plane event stream (0.42) — separate from Assist chat.

Protocol (JSON text frames)::

    ← hello
    → subscribe { id, types?, since_offset?, consumer?, session_id? }
    ← subscribed
    ← event { offset?, type, payload, ts }
    → ping / ← pong
    → unsubscribe

Catch-up: when ``since_offset`` is set and journal is available, replay then live.

0.58.8: optional **system session** filter (fan-in). Events match via
SessionService.event_matches (product door) — context, payload, or attached
instance. Cookie-like ``X-Palm-Session`` / ``palm_session`` binds the default
filter when subscribe omits session id.

0.58.17: product :func:`~palm.kits.server.middleware.resolve_session_service`
only — no raw session_plane on this path.
"""

from __future__ import annotations

import json
import logging
import queue
import threading
from typing import Any

from palm.common.events.catalog import (
    PUBLIC_EVENT_TYPES,
    catalog_dict,
    filter_public_types,
    is_public_event_type,
)
from plugins.kits.server.middleware import (
    extract_system_session_hint,
    resolve_session_service,
)
from bundles.standard.runtimes.server.surfaces.websocket.frames import (
    OP_CLOSE,
    OP_PING,
    OP_PONG,
    OP_TEXT,
    FrameReader,
    encode_close,
    encode_pong,
    encode_text,
)
from palm.system.subsystems.planes.session import looks_like_system_session_id

logger = logging.getLogger(__name__)

EVENTS_WS_PATH = "/ws/v1/events"
PROTOCOL_VERSION = 1


def run_events_websocket(
    *,
    rfile: object,
    wfile: object,
    ctx: Any,
    headers: dict[str, str] | None = None,
) -> None:
    """Serve one events WebSocket connection until close."""
    write_lock = threading.Lock()
    outbound: queue.Queue[dict[str, Any] | None] = queue.Queue()
    transport_hint = extract_system_session_hint(headers or {})
    sub_holder: dict[str, Any] = {
        "sub": None,
        "types": None,
        "closed": False,
        "session_id": None,
        "transport_session_hint": transport_hint,
    }

    def _send(obj: dict[str, Any]) -> None:
        if sub_holder["closed"]:
            return
        try:
            data = encode_text(json.dumps(obj, default=str))
            with write_lock:
                wfile.write(data)  # type: ignore[attr-defined]
                wfile.flush()  # type: ignore[attr-defined]
        except Exception:
            sub_holder["closed"] = True

    # Cookie-like bind: optional default system session on the connection
    if transport_hint and looks_like_system_session_id(transport_hint):
        svc = resolve_session_service(ctx)
        if svc is not None:
            try:
                bound = svc.bind_surface(
                    transport_hint,
                    create=True,
                    surface="websocket-events",
                    metadata={"via": "events_ws_cookie"},
                    origin="websocket-events",
                )
                sub_holder["session_id"] = str(bound.session_id)
            except Exception:
                logger.debug("events ws cookie bind failed", exc_info=True)

    _send(
        {
            "op": "hello",
            "protocol": PROTOCOL_VERSION,
            "channel": "events",
            "path": EVENTS_WS_PATH,
            "ops": ["hello", "subscribe", "unsubscribe", "ping"],
            "public_types": sorted(PUBLIC_EVENT_TYPES),
            "bound": {"session_id": sub_holder.get("session_id")},
            "session_filter": True,
        }
    )

    def _on_live(event: Any) -> None:
        et = str(getattr(event, "type", "") or "")
        if not is_public_event_type(et):
            return
        allowed = sub_holder.get("types")
        if allowed is not None and et not in allowed:
            return
        sid = sub_holder.get("session_id")
        if sid and not _event_matches_session(ctx, str(sid), event=event):
            return
        payload = dict(getattr(event, "payload", None) or {})
        outbound.put(
            {
                "op": "event",
                "type": et,
                "payload": payload,
                "id": getattr(event, "id", None),
                "live": True,
                "session_id": sid,
            }
        )

    def _writer() -> None:
        while not sub_holder["closed"]:
            try:
                item = outbound.get(timeout=0.5)
            except queue.Empty:
                continue
            if item is None:
                break
            _send(item)

    writer = threading.Thread(target=_writer, name="palm-ws-events-writer", daemon=True)
    writer.start()

    reader = FrameReader(rfile)
    try:
        while not sub_holder["closed"]:
            try:
                opcode, payload = reader.read_frame()
            except Exception:
                break
            if opcode == OP_CLOSE:
                break
            if opcode == OP_PING:
                with write_lock:
                    wfile.write(encode_pong(payload))  # type: ignore[attr-defined]
                    wfile.flush()  # type: ignore[attr-defined]
                continue
            if opcode == OP_PONG:
                continue
            if opcode != OP_TEXT:
                continue
            try:
                msg = json.loads(payload.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                _send({"op": "error", "error": "invalid_json"})
                continue
            if not isinstance(msg, dict):
                continue
            op = str(msg.get("op") or "")
            if op == "ping":
                _send({"op": "pong", "id": msg.get("id")})
                continue
            if op == "unsubscribe":
                _detach(ctx, sub_holder)
                _send({"op": "unsubscribed", "id": msg.get("id")})
                continue
            if op == "subscribe":
                _handle_subscribe(ctx, msg, sub_holder, _on_live, outbound, _send)
                continue
            if op in {"hello", ""}:
                continue
            _send({"op": "error", "error": "unknown_op", "op_in": op})
    finally:
        sub_holder["closed"] = True
        _detach(ctx, sub_holder)
        outbound.put(None)
        try:
            with write_lock:
                wfile.write(encode_close())  # type: ignore[attr-defined]
                wfile.flush()  # type: ignore[attr-defined]
        except Exception:
            pass


def _event_matches_session(
    ctx: Any,
    session_id: str,
    *,
    event: Any = None,
    payload: dict[str, Any] | None = None,
) -> bool:
    svc = resolve_session_service(ctx)
    if svc is None:
        # No product door: fall back to payload key equality only
        pay = payload
        if event is not None and pay is None:
            raw = getattr(event, "payload", None)
            pay = dict(raw) if isinstance(raw, dict) else {}
        pay = pay or {}
        if str(pay.get("session_id") or "") == session_id:
            return True
        ctx_obj = getattr(event, "context", None) if event is not None else None
        if ctx_obj is not None and str(getattr(ctx_obj, "session_id", "") or "") == session_id:
            return True
        return False
    return bool(svc.event_matches(session_id, event=event, payload=payload))


def _detach(ctx: Any, sub_holder: dict[str, Any]) -> None:
    sub = sub_holder.get("sub")
    sub_holder["sub"] = None
    if sub is None:
        return
    engine = _event_engine(ctx)
    if engine is None:
        return
    try:
        if isinstance(sub, list):
            for s in sub:
                if hasattr(engine, "unsubscribe"):
                    engine.unsubscribe(s)
                elif hasattr(s, "unsubscribe"):
                    s.unsubscribe()
        elif hasattr(sub, "unsubscribe"):
            sub.unsubscribe()
        elif hasattr(engine, "unsubscribe"):
            engine.unsubscribe(sub)
    except Exception:
        logger.debug("events ws detach failed", exc_info=True)


def _event_engine(ctx: Any) -> Any:
    if ctx is None:
        return None
    host = getattr(ctx, "host", None) or getattr(ctx, "_host", None)
    if host is not None and getattr(host, "event", None) is not None:
        return host.event
    # ApplicationHost-like
    if getattr(ctx, "event", None) is not None and not callable(getattr(ctx, "event", None)):
        return ctx.event
    return getattr(ctx, "event", None)


def _journal(ctx: Any) -> Any:
    if ctx is None:
        return None
    host = getattr(ctx, "host", None) or getattr(ctx, "_host", None)
    if host is not None:
        j = getattr(host, "event_journal", None)
        if j is not None:
            return j
    return getattr(ctx, "event_journal", None)


def _resolve_subscribe_session(
    ctx: Any,
    msg: dict[str, Any],
    sub_holder: dict[str, Any],
) -> str | None:
    """Session filter for this subscribe (message wins over cookie default).

    Edge key only: ``session_id`` (system subject, 0.58.9). Cookie/header
    default still applies when the message omits the key.
    """
    if "session_id" in msg:
        raw = msg.get("session_id")
        if raw is None or str(raw).strip() == "":
            return None
        text = str(raw).strip()
    else:
        # Keep connection default (cookie)
        fallback = sub_holder.get("session_id")
        if fallback is None or str(fallback).strip() == "":
            return None
        text = str(fallback).strip()

    svc = resolve_session_service(ctx)
    if svc is None:
        return text
    # System-shaped: bind via product door. Instance-shaped: reverse index.
    if looks_like_system_session_id(text):
        bound = svc.bind_surface(
            text,
            create=True,
            surface="websocket-events",
            metadata={"via": "events_ws_subscribe"},
            origin="websocket-events",
        )
        return str(bound.session_id)
    owner = svc.session_for_instance(text)
    if owner is not None:
        return str(owner.session_id)
    # Unknown non-system id: filter by raw text only (do not invent a session).
    return text


def _handle_subscribe(
    ctx: Any,
    msg: dict[str, Any],
    sub_holder: dict[str, Any],
    on_live: Any,
    outbound: queue.Queue,
    send: Any,
) -> None:
    raw_types = msg.get("types")
    types_list: list[str] | None = None
    if isinstance(raw_types, list):
        types_list = filter_public_types([str(t) for t in raw_types])
        if types_list is not None and len(types_list) == 0:
            send(
                {
                    "op": "error",
                    "id": msg.get("id"),
                    "error": "no_public_types",
                    "hint": "types must be from the public catalog",
                    "catalog": catalog_dict()["public_types"],
                }
            )
            return
    sub_holder["types"] = set(types_list) if types_list else None

    try:
        filter_sid = _resolve_subscribe_session(ctx, msg, sub_holder)
    except Exception as exc:
        send(
            {
                "op": "error",
                "id": msg.get("id"),
                "error": "session_bind",
                "message": str(exc),
            }
        )
        return
    sub_holder["session_id"] = filter_sid

    # Catch-up from journal
    since = msg.get("since_offset")
    journal = _journal(ctx)
    last_offset = 0
    if journal is not None and since is not None:
        try:
            after = int(since)
        except (TypeError, ValueError):
            after = 0
        try:
            entries = journal.read_after(after, limit=int(msg.get("limit") or 200))
        except Exception:
            entries = []
        for entry in entries:
            if isinstance(entry, dict):
                et = str(entry.get("event_type") or "")
                payload = dict(entry.get("payload") or {})
                off = int(entry.get("offset") or 0)
                eid = entry.get("id")
                ts = entry.get("timestamp")
            else:
                et = str(entry.event_type)
                payload = dict(entry.payload or {})
                off = int(entry.offset)
                eid = entry.id
                ts = entry.timestamp
            if not is_public_event_type(et):
                continue
            allowed = sub_holder.get("types")
            if allowed is not None and et not in allowed:
                continue
            if filter_sid and not _event_matches_session(
                ctx, str(filter_sid), payload=payload
            ):
                continue
            last_offset = max(last_offset, off)
            outbound.put(
                {
                    "op": "event",
                    "type": et,
                    "payload": payload,
                    "offset": off,
                    "id": eid,
                    "ts": ts,
                    "live": False,
                    "session_id": filter_sid,
                }
            )

    # Live subscription (handlers, not interceptors — avoid outbox re-entry quirks)
    _detach(ctx, sub_holder)
    engine = _event_engine(ctx)
    subs: list[Any] = []
    if engine is not None and hasattr(engine, "subscribe"):
        try:
            watch = (
                sorted(sub_holder["types"])
                if sub_holder.get("types")
                else sorted(PUBLIC_EVENT_TYPES)
            )
            for et in watch:
                subs.append(engine.subscribe(et, on_live))
            sub_holder["sub"] = subs
        except Exception:
            logger.exception("events ws live subscribe failed")

    send(
        {
            "op": "subscribed",
            "id": msg.get("id"),
            "types": sorted(sub_holder["types"])
            if sub_holder.get("types")
            else sorted(PUBLIC_EVENT_TYPES),
            "since_offset": msg.get("since_offset"),
            "catchup_last_offset": last_offset or None,
            "live": engine is not None,
            "journal": journal is not None,
            "session_id": filter_sid,
            "session_filter": filter_sid is not None,
        }
    )


__all__ = ["EVENTS_WS_PATH", "PROTOCOL_VERSION", "run_events_websocket"]
