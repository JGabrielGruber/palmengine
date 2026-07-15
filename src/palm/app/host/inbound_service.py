"""Inbound resource bindings — listen, enqueue WorkIntent when able (0.43)."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

from palm.common.resource.inbound import InboundSpec, parse_inbound_spec
from palm.core.work import WorkIntent

if TYPE_CHECKING:
    from palm.core.event import EventEngine
    from palm.definitions.resource import ResourceDefinition


@dataclass
class InboundBinding:
    """Active binding for one inbound-capable resource."""

    resource_name: str
    provider: str
    spec: InboundSpec
    definition: dict[str, Any] = field(default_factory=dict)
    status: str = "registered"  # registered | listening | error | stopped
    last_error: str | None = None
    last_signal_at: str | None = None
    signal_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "resource_name": self.resource_name,
            "provider": self.provider,
            "mode": self.spec.mode,
            "path": self.spec.path or self.resource_name,
            "enabled": self.spec.enabled,
            "work": self.spec.work.to_dict(),
            "status": self.status,
            "last_error": self.last_error,
            "last_signal_at": self.last_signal_at,
            "signal_count": self.signal_count,
        }


class InboundBindingService:
    """Scan resources with metadata.inbound; webhook map + optional stream workers."""

    def __init__(
        self,
        *,
        enqueue: Callable[[WorkIntent], str],
        event_engine: EventEngine | None = None,
        list_resources: Callable[[], list[dict[str, Any]]] | None = None,
        get_resource: Callable[[str], dict[str, Any] | None] | None = None,
    ) -> None:
        self._enqueue = enqueue
        self._event = event_engine
        self._list_resources = list_resources
        self._get_resource = get_resource
        self._bindings: dict[str, InboundBinding] = {}
        self._path_index: dict[str, str] = {}  # path slug → resource name
        self._debounce_until: dict[str, float] = {}
        self._lock = threading.RLock()
        self._stream_threads: dict[str, threading.Thread] = {}
        self._stream_stop = threading.Event()
        self._started = False

    def reload_from_definitions(self) -> int:
        """Rescan definition catalog for inbound-enabled resources."""
        if self._list_resources is None or self._get_resource is None:
            return 0
        rows = self._list_resources() or []
        found: dict[str, InboundBinding] = {}
        path_index: dict[str, str] = {}
        for row in rows:
            name = str(row.get("name") or row.get("id") or "").strip()
            if not name:
                continue
            detail = self._get_resource(name)
            if not isinstance(detail, dict):
                continue
            meta = detail.get("metadata")
            if not isinstance(meta, dict):
                # definition API may nest
                meta = (detail.get("resource") or {}).get("metadata") if isinstance(
                    detail.get("resource"), dict
                ) else None
            if not isinstance(meta, dict):
                meta = detail.get("metadata") if isinstance(detail.get("metadata"), dict) else {}
            # Prefer full metadata from verbose get
            if "inbound" not in (meta or {}):
                inner = detail.get("definition") or detail
                if isinstance(inner, dict) and isinstance(inner.get("metadata"), dict):
                    meta = inner["metadata"]
            spec = parse_inbound_spec(meta if isinstance(meta, dict) else {})
            if not spec or not spec.enabled or not spec.work.target:
                continue
            provider = str(
                detail.get("provider")
                or (detail.get("definition") or {}).get("provider")
                or row.get("provider")
                or ""
            )
            binding = InboundBinding(
                resource_name=name,
                provider=provider,
                spec=spec,
                definition=detail,
                status="registered",
            )
            found[name] = binding
            slug = (spec.path or name).strip().strip("/")
            path_index[slug] = name
            path_index[name] = name
        with self._lock:
            self._bindings = found
            self._path_index = path_index
        return len(found)

    def list_bindings(self) -> list[dict[str, Any]]:
        with self._lock:
            return [b.to_dict() for b in self._bindings.values()]

    def resolve(self, name_or_path: str) -> InboundBinding | None:
        key = str(name_or_path or "").strip().strip("/")
        with self._lock:
            if key in self._bindings:
                return self._bindings[key]
            mapped = self._path_index.get(key)
            if mapped and mapped in self._bindings:
                return self._bindings[mapped]
        return None

    def handle_webhook(
        self,
        name_or_path: str,
        *,
        body: dict[str, Any] | list[Any] | Any,
        headers: dict[str, str] | None = None,
        secret: str | None = None,
    ) -> dict[str, Any]:
        """Verify + enqueue WorkIntent. Returns 202-shaped dict or raises ValueError."""
        binding = self.resolve(name_or_path)
        if binding is None:
            raise KeyError(f"inbound resource not found: {name_or_path}")
        if binding.spec.mode != "webhook":
            raise ValueError(f"resource {binding.resource_name!r} is not mode=webhook")
        self._check_secret(binding, headers=headers or {}, provided=secret)
        envelope = self._normalize_envelope(binding, body)
        intent_id = self._signal(binding, envelope, source="webhook")
        return {
            "accepted": True,
            "resource": binding.resource_name,
            "intent_id": intent_id,
            "status": "enqueued" if intent_id else "coalesced_or_debounced",
        }

    def start_streams(self) -> int:
        """Start stream workers for mode=stream bindings (palm provider dogfood)."""
        self._stream_stop.clear()
        self._started = True
        n = 0
        with self._lock:
            items = list(self._bindings.items())
        for name, binding in items:
            if binding.spec.mode != "stream":
                continue
            if name in self._stream_threads and self._stream_threads[name].is_alive():
                continue
            t = threading.Thread(
                target=self._stream_loop,
                args=(name,),
                name=f"palm-inbound-stream-{name}",
                daemon=True,
            )
            self._stream_threads[name] = t
            t.start()
            n += 1
            with self._lock:
                if name in self._bindings:
                    self._bindings[name].status = "listening"
        return n

    def stop(self) -> None:
        self._stream_stop.set()
        self._started = False
        for t in list(self._stream_threads.values()):
            t.join(timeout=2.0)
        self._stream_threads.clear()
        with self._lock:
            for b in self._bindings.values():
                if b.status == "listening":
                    b.status = "stopped"

    def _stream_loop(self, resource_name: str) -> None:
        binding = self.resolve(resource_name)
        if binding is None:
            return
        # Palm origin stream: use journal poll client (robust) when provider=palm
        remote_url = self._remote_url(binding)
        if not remote_url:
            with self._lock:
                if resource_name in self._bindings:
                    self._bindings[resource_name].status = "error"
                    self._bindings[resource_name].last_error = "missing remote_url/url"
            return
        try:
            from palm.providers.palm.events_client import PalmEventsClient

            client = PalmEventsClient(remote_url)
            types = list(binding.spec.event_types) or None
            while not self._stream_stop.is_set():
                try:
                    events = client.poll(types=types, limit=50)
                    for ev in events:
                        if self._stream_stop.is_set():
                            break
                        envelope = {
                            "type": ev.get("type"),
                            "payload": ev.get("payload") or {},
                            "offset": ev.get("offset"),
                            "source": "stream",
                        }
                        self._signal(binding, envelope, source="stream")
                except Exception as exc:
                    with self._lock:
                        if resource_name in self._bindings:
                            self._bindings[resource_name].last_error = str(exc)
                            self._bindings[resource_name].status = "error"
                    time.sleep(2.0)
                    continue
                time.sleep(1.0)
        except Exception as exc:
            with self._lock:
                if resource_name in self._bindings:
                    self._bindings[resource_name].status = "error"
                    self._bindings[resource_name].last_error = str(exc)

    def _remote_url(self, binding: InboundBinding) -> str | None:
        if binding.spec.url:
            return binding.spec.url
        params = binding.definition.get("params")
        if not isinstance(params, dict):
            params = (binding.definition.get("definition") or {}).get("params") or {}
        if isinstance(params, dict):
            u = params.get("remote_url") or params.get("base_url")
            if u:
                return str(u)
        return None

    def _check_secret(
        self,
        binding: InboundBinding,
        *,
        headers: dict[str, str],
        provided: str | None,
    ) -> None:
        spec = binding.spec
        expected = None
        params = binding.definition.get("params")
        if not isinstance(params, dict):
            params = {}
        if spec.secret_param:
            expected = params.get(spec.secret_param)
        if expected is None and params.get("inbound_secret"):
            expected = params.get("inbound_secret")
        if not expected:
            return  # open dogfood
        header_name = (spec.secret_header or "X-Palm-Inbound-Secret").lower()
        got = provided
        if got is None:
            for k, v in headers.items():
                if k.lower() == header_name:
                    got = v
                    break
        if str(got or "") != str(expected):
            raise PermissionError("inbound secret mismatch")

    def _normalize_envelope(
        self, binding: InboundBinding, body: Any
    ) -> dict[str, Any]:
        if isinstance(body, dict):
            payload = dict(body)
        else:
            payload = {"value": body}
        return {
            "resource": binding.resource_name,
            "provider": binding.provider,
            "mode": binding.spec.mode,
            "payload": payload,
            "source": "webhook",
        }

    def _signal(
        self,
        binding: InboundBinding,
        envelope: dict[str, Any],
        *,
        source: str,
    ) -> str:
        from datetime import UTC, datetime

        spec = binding.spec
        # debounce
        if spec.debounce_seconds > 0:
            key = binding.resource_name
            now = time.monotonic()
            until = self._debounce_until.get(key, 0.0)
            if now < until:
                return ""
            self._debounce_until[key] = now + spec.debounce_seconds

        coalesce = spec.coalesce_key
        if not coalesce and spec.coalesce_field:
            payload = envelope.get("payload") if isinstance(envelope.get("payload"), dict) else {}
            field_val = payload.get(spec.coalesce_field) if isinstance(payload, dict) else None
            if field_val is not None:
                coalesce = f"inbound:{binding.resource_name}:{field_val}"
        if not coalesce:
            coalesce = f"inbound:{binding.resource_name}:{source}"

        kind = spec.work.kind if spec.work.kind in ("run_flow", "run_process") else "run_flow"
        target = spec.work.target
        intent = WorkIntent(
            kind=kind,
            target=target,
            payload={
                "inbound_resource": binding.resource_name,
                "inbound": envelope,
                "source": source,
            },
            coalesce_key=coalesce,
        )
        intent_id = self._enqueue(intent)

        with self._lock:
            b = self._bindings.get(binding.resource_name)
            if b is not None:
                b.signal_count += 1
                b.last_signal_at = datetime.now(UTC).isoformat()
                b.status = "listening" if source == "stream" else b.status
                b.last_error = None

        if self._event is not None:
            try:
                self._event.emit(
                    "inbound.received",
                    resource_ref=binding.resource_name,
                    source=source,
                    intent_id=intent_id or None,
                    work_target=target,
                )
            except Exception:
                pass
        return intent_id or ""


__all__ = ["InboundBinding", "InboundBindingService"]
