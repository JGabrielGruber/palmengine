"""
HTTP-layer middleware for server surfaces.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from palm.common.runtimes.base import BaseRuntime

PALM_SUBJECT_HEADER = "X-Palm-Subject"


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


def current_principal_id(runtime: BaseRuntime) -> str | None:
    principal = runtime.auth.principal
    return principal.id if principal is not None else None