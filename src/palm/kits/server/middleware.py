"""
HTTP-layer middleware for server surfaces.

Includes cookie-like **system session** transport (0.58.7): header or cookie
carry the system ``session_id``; the session plane owns truth.

**0.58.17 — single kit door:** product surfaces resolve
:func:`resolve_session_service` only. Do **not** call
:func:`resolve_session_plane` for product verbs (bind, gate, inspect,
continue resolve, event filter). The plane remains system law behind
:class:`~palm.services.session.SessionService`.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any

from palm.common.auth import current_principal_id

if TYPE_CHECKING:
    from palm.system.runtime.base import BaseRuntime

PALM_SUBJECT_HEADER = "X-Palm-Subject"
# Cookie-like bind transport for system session (0.58.7) — not product instance id.
PALM_SESSION_HEADER = "X-Palm-Session"
PALM_SESSION_COOKIE = "palm_session"


def authenticate_request(runtime: BaseRuntime, headers: Mapping[str, str]) -> bool:
    """
    Bind the request principal on the runtime auth engine.

    When ``auth_enforce`` is disabled, returns ``True`` without mutation.
    When enabled, requires ``X-Palm-Subject`` and authenticates via
    :class:`~palm.core.auth.AuthEngine`.
    """
    if not runtime.auth_enforce:
        return True

    subject = headers.get(PALM_SUBJECT_HEADER) or headers.get(PALM_SUBJECT_HEADER.lower())
    if not subject:
        return False

    runtime.auth.authenticate({"subject": subject})
    return runtime.auth.principal is not None


def parse_cookie_header(cookie_header: str | None) -> dict[str, str]:
    """Parse a Cookie header into name → value (last wins)."""
    if not cookie_header or not str(cookie_header).strip():
        return {}
    out: dict[str, str] = {}
    for part in str(cookie_header).split(";"):
        piece = part.strip()
        if not piece or "=" not in piece:
            continue
        name, _, value = piece.partition("=")
        name = name.strip()
        if name:
            out[name] = value.strip()
    return out


def extract_system_session_hint(headers: Mapping[str, str] | None) -> str | None:
    """Read system session id from cookie-like transport.

    Order:
    1. ``X-Palm-Session`` header
    2. Cookie ``palm_session``
    """
    if not headers:
        return None
    lower = {str(k).lower(): str(v) for k, v in headers.items()}
    header_val = (lower.get(PALM_SESSION_HEADER.lower()) or "").strip()
    if header_val:
        return header_val
    cookies = parse_cookie_header(lower.get("cookie"))
    cookie_val = (cookies.get(PALM_SESSION_COOKIE) or "").strip()
    return cookie_val or None


def set_cookie_header_value(
    session_id: str,
    *,
    path: str = "/",
    max_age: int | None = None,
    same_site: str = "Lax",
    http_only: bool = True,
) -> str:
    """Build a ``Set-Cookie`` value for the system session cookie (transport only)."""
    sid = str(session_id).strip()
    parts = [f"{PALM_SESSION_COOKIE}={sid}", f"Path={path}", f"SameSite={same_site}"]
    if http_only:
        parts.append("HttpOnly")
    if max_age is not None:
        parts.append(f"Max-Age={int(max_age)}")
    return "; ".join(parts)


def resolve_session_service(ctx: Any) -> Any | None:
    """Product :class:`~palm.services.session.SessionService` — **single kit door** (0.58.17).

    Surfaces (CLI / MCP / WS / REST) use this for all product session verbs:

    * bind / :meth:`~palm.services.session.SessionService.bind_surface`
    * continue resolve / owner gate / inspect / event filter
    * session metadata

    Order: ``ctx.session`` (product slot) → ``ctx.host.session`` →
    ``ctx._host.session``. Does **not** fall back to the raw session plane.
    """
    if ctx is None:
        return None
    for holder in (ctx, getattr(ctx, "host", None), getattr(ctx, "_host", None)):
        if holder is None:
            continue
        svc = getattr(holder, "session", None)
        if svc is None:
            continue
        # SessionService has plane(); AssistSessionService / method slots do not.
        if callable(getattr(svc, "plane", None)) or callable(
            getattr(svc, "bind_surface", None)
        ):
            return svc
        # ApplicationHost.session may be a property returning the door.
        if callable(svc) and not isinstance(svc, type):
            continue
    return None


def require_session_service(ctx: Any) -> Any:
    """Like :func:`resolve_session_service` but raises when the product door is missing."""
    svc = resolve_session_service(ctx)
    if svc is None:
        raise RuntimeError(
            "SessionService not available on context; surfaces must use the "
            "product door (0.58.17), not the raw session plane"
        )
    return svc


def resolve_session_plane(ctx: Any) -> Any | None:
    """Find :class:`~palm.system.subsystems.planes.session.SessionPlaneService` on host or runtime.

    **System / tests only.** Product surfaces must use
    :func:`resolve_session_service` (0.58.17). Prefer ``svc.plane()`` when
    you already hold the product door.
    """
    if ctx is None:
        return None
    plane = getattr(ctx, "session_plane", None)
    if plane is not None:
        return plane
    host = getattr(ctx, "host", None)
    if host is not None:
        plane = getattr(host, "session_plane", None)
        if plane is not None:
            return plane
    runtime = getattr(ctx, "runtime", None)
    if runtime is None:
        return None
    if callable(runtime):
        try:
            runtime = runtime()
        except Exception:
            return None
    return getattr(runtime, "session_plane", None)
