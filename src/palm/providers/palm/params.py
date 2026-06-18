"""Typed invoke parameters for the Palm compositional provider."""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any

from palm.core.resource.invocation import ResourceWaitOptions, WaitMode, parse_wait_mode
from palm.states import BlackboardState


@dataclass
class PalmInvokeParams:
    """Structured parameters for ``PalmProvider.invoke()`` and coordinators."""

    remote_url: str | None = None
    remote_token: str | None = None
    wait: bool = False
    wait_mode: str | None = None
    wait_timeout: float = 30.0
    max_depth: int = 8
    remote_retries: int = 2
    by_id: bool = False
    target_kind: str | None = None
    kind: str | None = None
    target: str | None = None
    flow_name: str | None = None
    process_name: str | None = None
    resource_ref: str | None = None
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    job_id: str | None = None
    initial_state: Any = None
    state: Any = None
    resource_action: str | None = None
    provider: str | None = None
    action: str | None = None
    resource_id: str | None = None
    parent_job_id: str | None = None
    extras: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(
        cls,
        params: dict[str, Any] | None = None,
        *,
        resource_id: str | None = None,
        **kwargs: Any,
    ) -> PalmInvokeParams:
        """Build typed params from a loose mapping (API-compatible with dict invoke)."""
        merged = dict(params or {})
        merged.update(kwargs)
        if resource_id is not None:
            merged.setdefault("resource_id", resource_id)
        if "__palm:parent_job_id" in merged:
            merged["parent_job_id"] = merged.pop("__palm:parent_job_id")

        known: dict[str, Any] = {}
        extras: dict[str, Any] = {}
        for key, value in merged.items():
            if key in _FIELD_NAMES:
                known[key] = value
            else:
                extras[key] = value

        wait_options = ResourceWaitOptions.from_params(merged)

        return cls(
            remote_url=_optional_str(known.get("remote_url")),
            remote_token=_optional_str(known.get("remote_token")),
            wait=wait_options.should_wait,
            wait_mode=wait_options.mode.value,
            wait_timeout=wait_options.timeout_seconds,
            max_depth=_as_int(known.get("max_depth"), default=8),
            remote_retries=_as_int(known.get("remote_retries"), default=2),
            by_id=_as_bool(known.get("by_id", False)),
            target_kind=_optional_str(known.get("target_kind")),
            kind=_optional_str(known.get("kind")),
            target=_optional_str(known.get("target")),
            flow_name=_optional_str(known.get("flow_name")),
            process_name=_optional_str(known.get("process_name")),
            resource_ref=_optional_str(known.get("resource_ref")),
            name=_optional_str(known.get("name")),
            metadata=dict(known.get("metadata") or {}),
            job_id=_optional_str(known.get("job_id")),
            initial_state=known.get("initial_state"),
            state=known.get("state"),
            resource_action=_optional_str(known.get("resource_action")),
            provider=_optional_str(known.get("provider")),
            action=_optional_str(known.get("action")),
            resource_id=_optional_str(known.get("resource_id")),
            parent_job_id=_optional_str(known.get("parent_job_id")),
            extras=extras,
        )

    @property
    def is_remote(self) -> bool:
        return bool(self.remote_url)

    @property
    def resolved_wait_mode(self) -> WaitMode:
        parsed = parse_wait_mode(self.wait_mode)
        if parsed is not None:
            return parsed
        if self.wait:
            return WaitMode.UNTIL_TERMINAL
        return WaitMode.FIRE_AND_FORGET

    @property
    def wait_options(self) -> ResourceWaitOptions:
        return ResourceWaitOptions(mode=self.resolved_wait_mode, timeout_seconds=self.wait_timeout)

    def resolve_job_id(self, *, resource_id: str | None = None) -> str:
        """Return the job id for ``fetch`` actions."""
        return str(self.job_id or self.target or resource_id or self.resource_id or "").strip()

    def correlation_metadata(self, *, depth: int, chain: tuple[str, ...]) -> dict[str, Any]:
        """Build child-job metadata with Palm correlation keys."""
        meta = dict(self.metadata)
        meta["__palm:invoke_depth"] = depth
        meta["__palm:invoke_chain"] = list(chain)
        if self.parent_job_id:
            meta["__palm:parent_job_id"] = str(self.parent_job_id)
        return meta

    def child_resource_params(self) -> dict[str, Any]:
        """Return passthrough params for nested ``invoke_resource`` calls."""
        child = dict(self.extras)
        if self.provider:
            child.setdefault("provider", self.provider)
        if self.resource_action:
            child.setdefault("resource_action", self.resource_action)
        if self.action:
            child.setdefault("action", self.action)
        if self.resource_id:
            child.setdefault("resource_id", self.resource_id)
        return child

    def resolve_state(self) -> BlackboardState | None:
        raw = self.initial_state or self.state
        if raw is None:
            return None
        if isinstance(raw, BlackboardState):
            return raw
        if isinstance(raw, dict):
            return BlackboardState(raw)
        return None

    def as_target_dict(self) -> dict[str, Any]:
        """Mapping shape expected by :func:`~palm.providers.palm.target.parse_target`."""
        return {
            "by_id": self.by_id,
            "target_kind": self.target_kind,
            "kind": self.kind,
            "target": self.target,
            "flow_name": self.flow_name,
            "process_name": self.process_name,
            "resource_ref": self.resource_ref,
            "name": self.name,
        }


_FIELD_NAMES = {item.name for item in fields(PalmInvokeParams)}


def _as_bool(value: Any) -> bool:
    return bool(value)


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
