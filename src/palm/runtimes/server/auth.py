"""
HTTP request authentication for :class:`~palm.runtimes.server.runtime.ServerRuntime`.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from palm.runtimes.server.runtime import ServerRuntime

PALM_SUBJECT_HEADER = "X-Palm-Subject"


def authenticate_request(runtime: ServerRuntime, headers: Mapping[str, str]) -> bool:
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


def current_principal_id(runtime: ServerRuntime) -> str | None:
    principal = runtime.auth.principal
    return principal.id if principal is not None else None
