"""
HTTP request authentication — backward-compatible re-exports.
"""

from __future__ import annotations

from palm.common.runtimes.server.middleware import (
    PALM_SUBJECT_HEADER,
    authenticate_request,
    current_principal_id,
)

__all__ = ["PALM_SUBJECT_HEADER", "authenticate_request", "current_principal_id"]