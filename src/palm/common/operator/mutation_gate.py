"""Mutation guard envelope — read vs drive signals for operator views."""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from typing import Any

_TERMINAL = frozenset({"SUCCEEDED", "SUCCESS", "FAILED", "CANCELLED"})
TOKEN_TTL_SECONDS = 3600
_DEV_SECRET = "palm-dev-mutation-secret"
_STRICT_ENV = "PALM_MCP_REQUIRE_INPUT_TOKEN"
_SECRET_ENV = "PALM_MUTATION_SECRET"


def mutation_secret() -> str:
    """Return the HMAC secret for input tokens (env override with dev default)."""
    raw = os.environ.get(_SECRET_ENV, "").strip()
    return raw or _DEV_SECRET


def require_input_token_enabled() -> bool:
    """True when strict mutation token enforcement is enabled."""
    raw = os.environ.get(_STRICT_ENV, "").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def issue_input_token(
    *,
    session_id: str,
    step_slug: str,
    secret: str,
    ttl_seconds: int = TOKEN_TTL_SECONDS,
) -> dict[str, str]:
    """Issue a CSRF-style token bound to session + step."""
    nonce = secrets.token_hex(8)
    issued_at = str(int(time.time()))
    digest = hmac.new(
        secret.encode(),
        f"{session_id}|{step_slug}|{nonce}|{issued_at}".encode(),
        hashlib.sha256,
    ).hexdigest()[:32]
    token = f"{nonce}.{issued_at}.{digest}"
    return {
        "input_token": token,
        "step_slug": step_slug,
        "expires_at": str(int(issued_at) + ttl_seconds),
    }


def validate_input_token(
    *,
    token: str | None,
    session_id: str,
    step_slug: str,
    secret: str,
    ttl_seconds: int = TOKEN_TTL_SECONDS,
) -> bool:
    """Validate a token issued for the current session step."""
    if not token:
        return False
    try:
        nonce, issued_at, digest = str(token).split(".", 2)
    except ValueError:
        return False
    try:
        issued = int(issued_at)
    except ValueError:
        return False
    if int(time.time()) > issued + ttl_seconds:
        return False
    expected = hmac.new(
        secret.encode(),
        f"{session_id}|{step_slug}|{nonce}|{issued_at}".encode(),
        hashlib.sha256,
    ).hexdigest()[:32]
    return hmac.compare_digest(expected, digest)


def build_mutation_envelope(
    inspect: dict[str, Any],
    *,
    session_id: str | None = None,
    secret: str | None = None,
    stored_gate: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a mutation guard block for operator inspect views."""
    status = str(inspect.get("status") or "").upper()
    step = inspect.get("step") or inspect.get("current_step_slug")
    step_kind = inspect.get("step_kind")
    field_type = inspect.get("field_type")
    waiting = status == "WAITING_FOR_INPUT"

    mutations_allowed = waiting and status not in _TERMINAL
    confirm_step = step_kind == "summary" or field_type == "confirm"

    payload: dict[str, Any] = {
        "mutations_allowed": mutations_allowed,
        "requires_user_input": mutations_allowed,
        "step_slug": step,
    }
    if confirm_step:
        payload["confirm_step"] = True
        payload["agent_hint"] = (
            "Confirm step: do not send yes/no unless the user explicitly said yes or no."
        )
    elif not mutations_allowed:
        payload["agent_hint"] = (
            "Read-only: use palm_flows_session or MCP resources; do not send value/input."
        )

    if mutations_allowed and session_id and secret:
        if (
            stored_gate
            and stored_gate.get("step_slug") == step
            and stored_gate.get("input_token")
        ):
            payload["input_token"] = stored_gate["input_token"]
        else:
            gate = issue_input_token(
                session_id=session_id,
                step_slug=str(step or ""),
                secret=secret,
            )
            payload["input_token"] = gate["input_token"]

    return {key: value for key, value in payload.items() if value is not None}


def persist_mutation_gate(repository: Any, instance_id: str, gate: dict[str, Any]) -> None:
    """Store the active mutation gate on instance metadata."""
    instance = repository.get(instance_id)
    meta = dict(instance.metadata or {})
    meta["mutation_gate"] = dict(gate)
    instance.metadata = meta
    repository.save(instance)


def refresh_mutation_gate(
    repository: Any,
    instance_id: str,
    inspect: dict[str, Any],
) -> dict[str, Any] | None:
    """Issue and persist a mutation gate when the session is waiting for input."""
    status = str(inspect.get("status") or "").upper()
    if status != "WAITING_FOR_INPUT":
        return None
    step = inspect.get("step") or inspect.get("current_step_slug") or ""
    secret = mutation_secret()
    gate = issue_input_token(
        session_id=instance_id,
        step_slug=str(step),
        secret=secret,
    )
    persist_mutation_gate(repository, instance_id, gate)
    return gate


def require_mutation_token(
    params: dict[str, Any],
    *,
    session_id: str,
    instance_metadata: dict[str, Any] | None,
    inspect: dict[str, Any],
) -> None:
    """Reject mutations without a valid token when strict mode is enabled."""
    if not require_input_token_enabled():
        return
    step = inspect.get("step") or inspect.get("current_step_slug") or ""
    token = params.get("input_token")
    secret = mutation_secret()
    stored = (instance_metadata or {}).get("mutation_gate") or {}
    if validate_input_token(
        token=token,
        session_id=session_id,
        step_slug=str(step),
        secret=secret,
    ):
        return
    if token and stored.get("input_token") == token and stored.get("step_slug") != step:
        raise ValueError(
            "mutation_rejected: stale input_token for prior step — "
            "re-inspect with palm_flows_session and pass input_token from mutation block"
        )
    raise ValueError(
        "mutation_rejected: missing or invalid input_token — "
        "re-inspect with palm_flows_session and pass input_token from mutation block"
    )


__all__ = [
    "TOKEN_TTL_SECONDS",
    "build_mutation_envelope",
    "issue_input_token",
    "mutation_secret",
    "persist_mutation_gate",
    "refresh_mutation_gate",
    "require_input_token_enabled",
    "require_mutation_token",
    "validate_input_token",
]