"""WebSocket Assist session loop — hello / ping / dispatch / bind (0.32.1+).

0.32.1: hello + ping/pong.
0.32.2: ``dispatch`` → same spine as MCP ``palm_assist`` → ``turn`` frames.
0.33.2: chat continuity (auto-start / intro / action rewrite) in assist.profiles.
0.58.7 / 0.58.9: bind law — ``op: bind`` / cookie-like headers resolve **session**
(``session_id`` = system subject). Continue handle is ``instance_id``
(product path residual SI-001).

0.58.17: product door only — :func:`~palm.kits.server.middleware.resolve_session_service`
+ :class:`~palm.services.session.BoundSurface`. No raw ``session_plane`` on this path.

Portal dogfood: ``session_id: null`` drops continue focus unless ``instance_id``
is in the same message. Dispatch refreshes BoundSurface from the mirrors.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any

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
from palm.system.subsystems.planes.session import (
    SessionClosedError,
    SessionNotFoundError,
    SessionPlaneError,
    looks_like_system_session_id,
)

if TYPE_CHECKING:
    from bundles.standard.runtimes.server.context import ServerContext

logger = logging.getLogger(__name__)

PROTOCOL_VERSION = 1
ASSIST_WS_PATH = "/ws/v1/assist"
MAX_MESSAGE_BYTES = 256 * 1024


def run_assist_websocket(
    *,
    rfile: object,
    wfile: object,
    ctx: ServerContext | None = None,
    headers: dict[str, str] | None = None,
) -> None:
    """Blocking assist channel after HTTP upgrade has completed."""
    conn = _ConnectionState(headers=headers or {})
    # Cookie-like bind at upgrade time when plane is available
    _ensure_system_session(conn, ctx=ctx, create=True)
    reader = FrameReader(rfile)
    version = _palm_version()
    _send_json(
        wfile,
        {
            "op": "hello",
            "protocol": PROTOCOL_VERSION,
            "server": "palm",
            "version": version,
            "channel": "assist",
            "path": ASSIST_WS_PATH,
            "ops": ["hello", "ping", "dispatch", "bind"],
            "auth": {"mode": conn.auth_mode, "subject": conn.subject},
            "bound": conn.bound_snapshot(),
        },
    )

    while True:
        try:
            opcode, payload = reader.read_frame()
        except ConnectionError:
            break
        except OSError:
            break

        if opcode == OP_CLOSE:
            try:
                wfile.write(encode_close())  # type: ignore[attr-defined]
                wfile.flush()  # type: ignore[attr-defined]
            except OSError:
                pass
            break
        if opcode == OP_PING:
            try:
                wfile.write(encode_pong(payload))  # type: ignore[attr-defined]
                wfile.flush()  # type: ignore[attr-defined]
            except OSError:
                break
            continue
        if opcode == OP_PONG:
            continue
        if opcode != OP_TEXT:
            _send_json(
                wfile,
                {
                    "op": "error",
                    "id": None,
                    "error": {
                        "code": "unsupported_opcode",
                        "message": f"unsupported websocket opcode {opcode}",
                    },
                },
            )
            continue

        if len(payload) > MAX_MESSAGE_BYTES:
            _send_json(
                wfile,
                {
                    "op": "error",
                    "id": None,
                    "error": {
                        "code": "message_too_large",
                        "message": f"max message size is {MAX_MESSAGE_BYTES} bytes",
                    },
                },
            )
            continue

        try:
            message = json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            _send_json(
                wfile,
                {
                    "op": "error",
                    "id": None,
                    "error": {"code": "invalid_json", "message": str(exc)},
                },
            )
            continue

        if not isinstance(message, dict):
            _send_json(
                wfile,
                {
                    "op": "error",
                    "id": None,
                    "error": {
                        "code": "invalid_request",
                        "message": "JSON object required",
                    },
                },
            )
            continue

        response = handle_client_message(message, ctx=ctx, conn=conn)
        if response is None:
            continue
        _send_json(wfile, response)


class _ConnectionState:
    """Per-connection bind state (0.32.3 + 0.58.7/0.58.9 + BoundSurface 0.58.17)."""

    def __init__(self, *, headers: dict[str, str]) -> None:
        # Session-owned surface context (truth). Dual slots below are transport mirrors.
        self.bound: Any | None = None  # BoundSurface | None
        # System outside subject — edge name session_id (mirrors bound.session_id).
        self.session_id: str | None = None
        # Product continue handle (instance id) — SI-001 residual.
        self.instance_id: str | None = None
        self.flow_id: str | None = None
        self.client: str | None = None
        self.session_created: bool = False
        lower = {k.lower(): v for k, v in headers.items()}
        auth = lower.get("authorization", "")
        if auth.lower().startswith("bearer ") and auth[7:].strip():
            self.auth_mode = "bearer"
            self.subject = auth[7:].strip()[:64]
        else:
            self.auth_mode = "open"
            self.subject = lower.get("x-palm-subject") or "anonymous"
        # Cookie / X-Palm-Session hint (product bind deferred until ctx known)
        hint = extract_system_session_hint(headers)
        self._transport_session_hint: str | None = hint

    def apply_bound(self, bound: Any, *, created: bool = False) -> None:
        """Install a BoundSurface as the connection truth."""
        self.bound = bound
        self.session_id = str(bound.session_id) if bound is not None else None
        if bound is not None and getattr(bound, "instance_id", None):
            self.instance_id = str(bound.instance_id)
        self.session_created = bool(created)

    def clear_bound(self) -> None:
        self.bound = None
        self.session_id = None
        self.instance_id = None
        self.flow_id = None
        self.session_created = False
        self._transport_session_hint = None

    def bound_snapshot(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "session_id": self.session_id,
            "instance_id": self.instance_id,
            "flow_id": self.flow_id,
        }
        if self.bound is not None and hasattr(self.bound, "to_dict"):
            out["bound_surface"] = self.bound.to_dict()
        return out


def handle_client_message(
    message: dict[str, Any],
    *,
    ctx: ServerContext | None = None,
    conn: _ConnectionState | None = None,
) -> dict[str, Any] | None:
    """Handle one client JSON message; return server frame or None."""
    op = message.get("op")
    msg_id = message.get("id")
    state = conn or _ConnectionState(headers={})

    if op == "hello":
        if message.get("client") is not None:
            state.client = str(message.get("client"))
        # Optional system / product bind on hello for reconnect
        _apply_message_bind_fields(message, state, ctx=ctx, create=True)
        # Transport hint if still unbound
        _ensure_system_session(state, ctx=ctx, create=True)
        return {
            "op": "hello",
            "id": msg_id,
            "protocol": PROTOCOL_VERSION,
            "server": "palm",
            "version": _palm_version(),
            "channel": "assist",
            "ack": True,
            "client": state.client or message.get("client"),
            "ops": ["hello", "ping", "dispatch", "bind"],
            "bound": state.bound_snapshot(),
            "auth": {"mode": state.auth_mode},
        }

    if op == "ping":
        return {"op": "pong", "id": msg_id}

    if op == "bind":
        return _handle_bind(message, state, ctx=ctx)

    if op == "dispatch":
        return _handle_dispatch(message, ctx=ctx, conn=state)

    return {
        "op": "error",
        "id": msg_id,
        "error": {
            "code": "unknown_op",
            "message": f"unknown op {op!r}",
        },
    }


def _handle_bind(
    message: dict[str, Any],
    conn: _ConnectionState,
    *,
    ctx: object | None = None,
) -> dict[str, Any]:
    """Bind system session (SessionService) + optional product instance / flow."""
    msg_id = message.get("id")
    if message.get("clear") in (True, "true", "1", 1):
        conn.clear_bound()

    try:
        _apply_message_bind_fields(message, conn, ctx=ctx, create=_create_flag(message))
    except SessionClosedError as exc:
        return {
            "op": "error",
            "id": msg_id,
            "error": {"code": "session_closed", "message": str(exc)},
        }
    except SessionNotFoundError as exc:
        return {
            "op": "error",
            "id": msg_id,
            "error": {"code": "session_not_found", "message": str(exc)},
        }
    except SessionPlaneError as exc:
        return {
            "op": "error",
            "id": msg_id,
            "error": {"code": "session_bind", "message": str(exc)},
        }

    # Default: ensure a system subject exists when product door is available
    if conn.session_id is None and "session_id" not in message:
        create = _create_flag(message)
        if create is not False:
            _ensure_system_session(conn, ctx=ctx, create=True)

    return {
        "op": "bound",
        "id": msg_id,
        **conn.bound_snapshot(),
        "created": conn.session_created,
    }


def _create_flag(message: dict[str, Any]) -> bool:
    raw = message.get("create")
    if raw in (False, "false", "0", 0):
        return False
    return True


def _apply_message_bind_fields(
    message: dict[str, Any],
    conn: _ConnectionState,
    *,
    ctx: object | None,
    create: bool,
) -> None:
    """Apply session / instance / flow fields from hello or bind message.

    0.58.9: ``session_id`` is always the system subject. ``instance_id`` is the
    product continue handle. Instance-shaped values under ``session_id`` are
    treated as ``instance_id`` (product residual), not promoted to system.
    """
    if "session_id" in message:
        raw_sid = message.get("session_id")
        if raw_sid is None or str(raw_sid).strip() == "":
            conn.bound = None
            conn.session_id = None
            conn.session_created = False
            # Unbind subject also drops continue focus unless this
            # message sets instance_id explicitly.
            if "instance_id" not in message:
                conn.instance_id = None
        else:
            sid = str(raw_sid).strip()
            if looks_like_system_session_id(sid):
                _service_bind_into(conn, sid, ctx=ctx, create=create)
            else:
                # Product lie residual — store as instance, do not bind as system.
                conn.instance_id = sid

    if "instance_id" in message:
        raw_iid = message.get("instance_id")
        if raw_iid is None or str(raw_iid).strip() == "":
            conn.instance_id = None
            if conn.bound is not None:
                conn.bound = conn.bound.with_instance(None)
        else:
            iid = str(raw_iid).strip() or None
            conn.instance_id = iid
            if conn.bound is not None and iid:
                conn.bound = conn.bound.with_instance(iid)

    if "flow_id" in message:
        raw_fid = message.get("flow_id")
        if raw_fid is None or str(raw_fid).strip() == "":
            conn.flow_id = None
        else:
            conn.flow_id = str(raw_fid).strip() or None


def _service_bind_into(
    conn: _ConnectionState,
    session_id: str | None,
    *,
    ctx: object | None,
    create: bool = True,
    instance_id: str | None = None,
) -> None:
    """Bind via product SessionService (0.58.17); store BoundSurface as truth."""
    svc = resolve_session_service(ctx)
    if svc is None:
        # Transport-only mirror when host not fully wired (tests / early boot).
        if session_id:
            conn.session_id = session_id
            conn.session_created = False
            if instance_id:
                conn.instance_id = instance_id
        return
    iid = instance_id if instance_id is not None else conn.instance_id
    sid_hint = (session_id or "").strip() or None
    existed = (
        looks_like_system_session_id(sid_hint) and svc.get(sid_hint) is not None
    )
    bound = svc.bind_surface(
        sid_hint,
        create=create,
        surface="websocket",
        metadata={"via": "ws_bind"},
        origin="websocket",
        instance_id=iid,
        resolve_instance=iid is None,
    )
    conn.apply_bound(bound, created=not existed)


def _sync_bound_from_mirrors(
    conn: _ConnectionState,
    *,
    ctx: object | None,
) -> None:
    """Keep BoundSurface snapshot aligned with session/instance mirrors."""
    if conn.bound is not None and str(conn.bound.session_id) != str(conn.session_id or ""):
        conn.bound = None
    if conn.bound is not None:
        conn.bound = conn.bound.with_instance(conn.instance_id)
    svc = resolve_session_service(ctx)
    if svc is None or not conn.session_id or not looks_like_system_session_id(
        conn.session_id
    ):
        return
    if conn.instance_id:
        try:
            bound = svc.focus(conn.session_id, conn.instance_id)
            conn.apply_bound(bound, created=False)
            return
        except Exception:
            logger.debug("ws turn focus skipped", exc_info=True)
    if conn.bound is None:
        try:
            _service_bind_into(
                conn,
                conn.session_id,
                ctx=ctx,
                create=False,
                instance_id=conn.instance_id,
            )
        except Exception:
            logger.debug("ws turn rebind skipped", exc_info=True)


def _ensure_system_session(
    conn: _ConnectionState,
    *,
    ctx: object | None,
    create: bool = True,
) -> None:
    """Ensure connection has a system session via product door when available."""
    svc = resolve_session_service(ctx)
    if conn.session_id:
        if svc is not None:
            try:
                bound = svc.bind_surface(
                    conn.session_id,
                    create=False,
                    surface="websocket",
                    origin="websocket",
                    instance_id=conn.instance_id,
                    resolve_instance=conn.instance_id is None,
                )
                conn.apply_bound(bound, created=False)
            except SessionNotFoundError:
                if create:
                    _service_bind_into(conn, None, ctx=ctx, create=True)
            except SessionClosedError:
                if create:
                    _service_bind_into(conn, None, ctx=ctx, create=True)
        return

    hint = conn._transport_session_hint
    if hint:
        try:
            _service_bind_into(conn, hint, ctx=ctx, create=create)
            if conn.session_id:
                return
        except (SessionClosedError, SessionNotFoundError, SessionPlaneError):
            if not create:
                raise
    if create:
        _service_bind_into(conn, None, ctx=ctx, create=True)


def _handle_dispatch(
    message: dict[str, Any],
    *,
    ctx: ServerContext | None,
    conn: _ConnectionState | None = None,
) -> dict[str, Any]:
    """Run assist meta-dispatch (same spine as MCP palm_assist) → turn/error."""
    msg_id = message.get("id")
    state = conn or _ConnectionState(headers={})
    if ctx is None:
        return {
            "op": "error",
            "id": msg_id,
            "error": {
                "code": "unavailable",
                "message": "server context not available for dispatch",
            },
        }

    path_raw = message.get("path")
    alias = message.get("alias")
    params = message.get("params")
    if params is None:
        params = {}
    if not isinstance(params, dict):
        return {
            "op": "error",
            "id": msg_id,
            "error": {
                "code": "validation",
                "message": "params must be an object",
            },
        }
    params = dict(params)
    # Allow top-level convenience keys (chat clients)
    for key in (
        "value",
        "input",
        "session_id",
        "instance_id",
        "flow_id",
        "body",
        "query",
        "q",
    ):
        if key in message and key not in params:
            params[key] = message[key]

    # Ensure system subject before work; inject into params for flow submit
    try:
        _ensure_system_session(state, ctx=ctx, create=True)
    except SessionPlaneError as exc:
        return {
            "op": "error",
            "id": msg_id,
            "error": {"code": "session_bind", "message": str(exc)},
        }

    # 0.58.9: session_id = system; instance_id = continue handle
    if state.session_id and not params.get("session_id"):
        params["session_id"] = state.session_id
    if state.instance_id and not params.get("instance_id"):
        params["instance_id"] = state.instance_id
    if not params.get("flow_id") and state.flow_id:
        params["flow_id"] = state.flow_id
    # 0.32.6 — Portal needs structured input; service builds it when this is set
    params.setdefault("include_input_schema", True)

    path_list: list[str] | None = None
    if isinstance(path_raw, list):
        path_list = [str(p) for p in path_raw]
    elif path_raw is not None:
        return {
            "op": "error",
            "id": msg_id,
            "error": {
                "code": "validation",
                "message": "path must be an array of strings",
            },
        }

    try:
        from bundles.standard.runtimes.mcp.assist.dispatch import (
            dispatch_operator_path,
            normalize_assist_dispatch_args,
            resolve_dispatch_path,
            shape_dispatch_result,
        )
        from palm.services.assist.profiles.continuity import apply_chat_continuity
        from palm.services.assist.profiles.turn_meta import flow_id_from_turn
        from palm.services.assist.views import ensure_assist_view_registration

        ensure_assist_view_registration()
        norm_path, norm_alias, dispatch_params, _used_default = (
            normalize_assist_dispatch_args(
                path=path_list,
                alias=str(alias) if alias is not None else None,
                params=params,
            )
        )
        resolved = resolve_dispatch_path(
            path=norm_path,
            alias=norm_alias,
            params=dispatch_params,
        )
        raw = dispatch_operator_path(ctx, resolved, dispatch_params)
        view_format = str(message.get("format") or "assistant")
        # After create, re-inspect so first turn includes input schema (Portal).
        # Product path keys by instance_id (SI-001); rewrite resolves sess- if needed.
        if (
            view_format == "assistant"
            and len(resolved) >= 2
            and resolved[0] == "flows"
            and resolved[-1] == "create"
            and isinstance(raw, dict)
        ):
            flow_id = resolved[1]
            inspect_key = raw.get("instance_id") or raw.get("session_id")
            if inspect_key:
                inspect_path = ["flows", flow_id, "instance", str(inspect_key)]
                try:
                    raw = dispatch_operator_path(
                        ctx,
                        inspect_path,
                        {"format": "assistant"},
                    )
                    resolved = inspect_path
                except Exception:
                    logger.debug(
                        "ws create re-inspect failed; using create envelope",
                        exc_info=True,
                    )
        shaped = shape_dispatch_result(
            resolved,
            raw,
            format=view_format,
            params=dispatch_params,
            tool_format=view_format,
            include_input_schema=True,  # Portal dynamic widgets (not on MCP)
        )
        # 0.33.2 — chat policy lives in assist.profiles (transport only injects dispatch)
        if view_format == "assistant":

            def _dispatch(path: list[str], p: dict[str, Any]) -> Any:
                return dispatch_operator_path(ctx, path, p)

            def _shape(path: list[str], result: Any, **kwargs: Any) -> dict[str, Any]:
                return shape_dispatch_result(path, result, **kwargs)

            shaped = apply_chat_continuity(
                shaped,
                dispatch_params,
                dispatch=_dispatch,
                shape=_shape,
            )
        # Refresh bind from turn: session_id = system; instance_id = continue
        system_sid = shaped.get("session_id")
        turn_refs = shaped.get("refs")
        if not looks_like_system_session_id(system_sid) and isinstance(turn_refs, dict):
            system_sid = turn_refs.get("session_id")
        if looks_like_system_session_id(system_sid):
            state.session_id = str(system_sid).strip()
        instance_id = shaped.get("instance_id")
        if (not instance_id or looks_like_system_session_id(instance_id)) and isinstance(
            turn_refs, dict
        ):
            instance_id = turn_refs.get("instance_id")
        if instance_id and not looks_like_system_session_id(instance_id):
            state.instance_id = str(instance_id)
        _sync_bound_from_mirrors(state, ctx=ctx)
        flow = flow_id_from_turn(shaped)
        if flow:
            state.flow_id = str(flow)
            refs = shaped.get("refs")
            if not isinstance(refs, dict):
                refs = {}
                shaped["refs"] = refs
            refs.setdefault("flow_id", state.flow_id)
            if state.session_id:
                refs.setdefault("session_id", state.session_id)
            if state.instance_id:
                refs.setdefault("instance_id", state.instance_id)
        if state.session_id and isinstance(shaped, dict):
            shaped.setdefault("session_id", state.session_id)
        if state.instance_id and isinstance(shaped, dict):
            shaped.setdefault("instance_id", state.instance_id)
        return {
            "op": "turn",
            "id": msg_id,
            "payload": shaped,
            "bound": state.bound_snapshot(),
        }
    except ValueError as exc:
        return {
            "op": "error",
            "id": msg_id,
            "error": {"code": "validation", "message": str(exc)},
        }
    except Exception as exc:
        # SI-015 / 0.58.15: map attribution refusal to stable client codes
        from palm.system.subsystems.planes.session import (
            InstanceNotOwnedError,
            SessionAttributionError,
        )
        refused = structure_refuse_voice(msg_id, exc)
        if refused is not None:
            return refused
        if isinstance(exc, InstanceNotOwnedError):
            return {
                "op": "error",
                "id": msg_id,
                "error": {"code": "session_owner", "message": str(exc)},
            }
        if isinstance(exc, SessionAttributionError):
            return {
                "op": "error",
                "id": msg_id,
                "error": {"code": "session_attribution", "message": str(exc)},
            }
        logger.exception("websocket assist dispatch failed")
        return {
            "op": "error",
            "id": msg_id,
            "error": {
                "code": "internal",
                "message": str(exc) or exc.__class__.__name__,
            },
        }


def _send_json(wfile: object, payload: dict[str, Any]) -> None:
    data = encode_text(json.dumps(payload, separators=(",", ":")))
    wfile.write(data)  # type: ignore[attr-defined]
    wfile.flush()  # type: ignore[attr-defined]


def _palm_version() -> str:
    try:
        from palm import __version__

        return str(__version__)
    except Exception:
        return "unknown"


def structure_refuse_voice(msg_id: str, exc: BaseException) -> dict[str, Any] | None:
    """Map ready / organ refuse to Assist WS error payload; else ``None``."""
    from palm.system.structure.errors import (
        AdmissionRefusedError,
        CapabilityRefusedError,
    )

    if isinstance(exc, AdmissionRefusedError):
        code = "admission_refused"
    elif isinstance(exc, CapabilityRefusedError):
        code = "capability_refused"
    else:
        return None
    return {
        "op": "error",
        "id": msg_id,
        "error": {"code": code, "message": str(exc)},
    }


__all__ = [
    "ASSIST_WS_PATH",
    "PROTOCOL_VERSION",
    "handle_client_message",
    "run_assist_websocket",
    "structure_refuse_voice",
]
