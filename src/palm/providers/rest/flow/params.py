"""Typed invoke parameters for the REST provider."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any


@dataclass
class RestInvokeParams:
    """Structured parameters for REST provider invocations."""

    base_url: str | None = None
    method: str = "GET"
    headers: dict[str, str] = field(default_factory=dict)
    timeout: float = 10.0
    retries: int = 2
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, params: dict[str, Any] | None = None, **kwargs: Any) -> RestInvokeParams:
        merged = dict(params or {})
        merged.update(kwargs)
        known: dict[str, Any] = {}
        extras: dict[str, Any] = {}
        for key, value in merged.items():
            if key in _FIELD_NAMES:
                known[key] = value
            else:
                extras[key] = value
        headers = known.get("headers") or {}
        return cls(
            base_url=_optional_str(known.get("base_url")),
            method=str(known.get("method") or "GET").upper(),
            headers={str(k): str(v) for k, v in dict(headers).items()},
            timeout=_as_float(known.get("timeout_seconds", known.get("timeout")), default=10.0),
            retries=_as_int(known.get("retries"), default=2),
            extras=extras,
        )

    def resolve_url(self, resource_id: str) -> str:
        if resource_id.startswith("http://") or resource_id.startswith("https://"):
            return resource_id
        if not self.base_url:
            raise ValueError("rest fetch requires base_url param or absolute resource_id URL")
        base = self.base_url.rstrip("/")
        path = resource_id.lstrip("/")
        return f"{base}/{path}" if path else base


_FIELD_NAMES = {item.name for item in fields(RestInvokeParams)}


def _as_float(value: Any, *, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, *, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _optional_str(value: Any) -> str | None:
    return str(value) if value is not None else None
