"""Product session domain — surface door over the system session plane (0.58.12+).

0.58.14: :class:`BoundSurface` is the session-owned surface context handle.
"""

from services.session.bound_surface import (
    SESSION_CONTEXT_KEYS,
    BoundSurface,
    derive_session_kind,
    derive_session_origin,
)
from services.session.service import (
    HOST_SESSION_ID,
    HOST_SESSION_ORIGIN,
    WORK_DRAIN_ORIGIN,
    ContinueTarget,
    SessionAttributionError,
    SessionService,
    looks_like_system_session_id,
    new_session_id,
    service_session_id,
)

__all__ = [
    "SESSION_CONTEXT_KEYS",
    "BoundSurface",
    "ContinueTarget",
    "HOST_SESSION_ID",
    "HOST_SESSION_ORIGIN",
    "SessionAttributionError",
    "SessionService",
    "WORK_DRAIN_ORIGIN",
    "derive_session_kind",
    "derive_session_origin",
    "looks_like_system_session_id",
    "new_session_id",
    "service_session_id",
]
