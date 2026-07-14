"""WebSocket control-plane event stream (0.42) — separate from Assist chat.

Protocol (JSON text frames)::

    ← hello
    → subscribe { id, types?, since_offset?, consumer? }
    ← subscribed
    ← event { offset?, type, payload, ts }
    → ping / ← pong
    → unsubscribe

Catch-up: when ``since_offset`` is set and journal is available, replay then live.
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
from palm.runtimes.server.surfaces.websocket.frames import (
    OP_CLOSE,
    OP_PING,
    OP_PONG,
    OP_TEXT,
    FrameReader,
    encode_close,
    encode_pong,
    encode_text,
)

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
    del headers
    write_lock = threading.Lock()
    outbound: queue.Queue[dict[str, Any] | None] = queue.Queue()
    sub_holder: dict[str, Any] = {"sub": None, "types": None, "closed": False}

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

    _send(
        {
            "op": "hello",
            "protocol": PROTOCOL_VERSION,
            "channel": "events",
            "path": EVENTS_WS_PATH,
            "ops": ["hello", "subscribe", "unsubscribe", "ping"],
            "public_types": sorted(PUBLIC_EVENT_TYPES),
        }
    )

    def _on_live(event: Any) -> None:
        et = str(getattr(event, "type", "") or "")
        if not is_public_event_type(et):
            return
        allowed = sub_holder.get("types")
        if allowed is not None and et not in allowed:
            return
        payload = dict(getattr(event, "payload", None) or {})
        outbound.put(
            {
                "op": "event",
                "type": et,
                "payload": payload,
                "id": getattr(event, "id", None),
                "live": True,
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
        }
    )


__all__ = ["EVENTS_WS_PATH", "PROTOCOL_VERSION", "run_events_websocket"]
