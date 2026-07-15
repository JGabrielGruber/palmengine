"""Inbound resource bindings — listen, persist, enqueue WorkIntent when able (0.43+)."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from palm.common.resource.inbound import InboundSpec, parse_inbound_spec
from palm.core.work import WorkIntent

if TYPE_CHECKING:
    from palm.core.event import EventEngine

_DEFAULT_POLL_INTERVAL = 5.0
_BACKGROUND_MODES = frozenset({"stream", "poll"})


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
        out: dict[str, Any] = {
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
        if self.spec.store_resource:
            out["store_resource"] = self.spec.store_resource
        if self.spec.store_action:
            out["store_action"] = self.spec.store_action
        return out


class InboundBindingService:
    """Scan resources with metadata.inbound; webhook + background stream/poll workers."""

    def __init__(
        self,
        *,
        enqueue: Callable[[WorkIntent], str],
        event_engine: EventEngine | None = None,
        list_resources: Callable[[], list[dict[str, Any]]] | None = None,
        get_resource: Callable[[str], dict[str, Any] | None] | None = None,
        invoke_resource: Callable[..., Any] | None = None,
    ) -> None:
        self._enqueue = enqueue
        self._event = event_engine
        self._list_resources = list_resources
        self._get_resource = get_resource
        self._invoke_resource = invoke_resource
        self._bindings: dict[str, InboundBinding] = {}
        self._path_index: dict[str, str] = {}  # path slug → resource name
        self._debounce_until: dict[str, float] = {}
        self._lock = threading.RLock()
        self._worker_threads: dict[str, threading.Thread] = {}
        self._worker_stop = threading.Event()
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
            meta = _definition_metadata(detail)
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
        envelope = self._normalize_envelope(binding, body, source="webhook")
        intent_id, store_meta = self._signal(binding, envelope, source="webhook")
        return {
            "accepted": True,
            "resource": binding.resource_name,
            "intent_id": intent_id,
            "status": "enqueued" if intent_id else "coalesced_or_debounced",
            **store_meta,
        }

    def start_workers(self) -> int:
        """Start background workers for mode=stream and mode=poll bindings."""
        self._worker_stop.clear()
        self._started = True
        n = 0
        with self._lock:
            items = list(self._bindings.items())
        for name, binding in items:
            if binding.spec.mode not in _BACKGROUND_MODES:
                continue
            if name in self._worker_threads and self._worker_threads[name].is_alive():
                continue
            target = (
                self._stream_loop if binding.spec.mode == "stream" else self._poll_loop
            )
            t = threading.Thread(
                target=target,
                args=(name,),
                name=f"palm-inbound-{binding.spec.mode}-{name}",
                daemon=True,
            )
            self._worker_threads[name] = t
            t.start()
            n += 1
            with self._lock:
                if name in self._bindings:
                    self._bindings[name].status = "listening"
        return n

    def start_streams(self) -> int:
        """Backward-compatible alias for :meth:`start_workers`."""
        return self.start_workers()

    def stop(self) -> None:
        self._worker_stop.set()
        self._started = False
        for t in list(self._worker_threads.values()):
            t.join(timeout=2.0)
        self._worker_threads.clear()
        with self._lock:
            for b in self._bindings.values():
                if b.status == "listening":
                    b.status = "stopped"

    def _stream_loop(self, resource_name: str) -> None:
        binding = self.resolve(resource_name)
        if binding is None:
            return
        remote_url = self._remote_url(binding)
        if not remote_url:
            with self._lock:
                if resource_name in self._bindings:
                    self._bindings[resource_name].status = "error"
                    self._bindings[resource_name].last_error = "missing remote_url/url"
            return
        if self._stream_loop_ws(binding, resource_name, remote_url):
            return
        self._stream_loop_http(binding, resource_name, remote_url)

    def _stream_loop_ws(
        self, binding: InboundBinding, resource_name: str, remote_url: str
    ) -> bool:
        """Return True when WS loop ran (even if it ended with error after connect)."""
        try:
            from palm.providers.palm.events_ws import PalmEventsWebSocketClient
        except Exception:
            return False
        types = list(binding.spec.event_types) or None
        try:
            client = PalmEventsWebSocketClient(remote_url)
            client.subscribe(types=types, since_offset=0)
            while not self._worker_stop.is_set():
                try:
                    for ev in client.events(timeout=1.0):
                        if self._worker_stop.is_set():
                            break
                        if ev.get("op") != "event":
                            continue
                        envelope = {
                            "type": ev.get("type"),
                            "payload": ev.get("payload") or {},
                            "offset": ev.get("offset"),
                            "source": "stream",
                            "transport": "websocket",
                        }
                        self._signal(binding, envelope, source="stream")
                except (TimeoutError, ConnectionError):
                    if self._worker_stop.is_set():
                        break
                    continue
                except Exception as exc:
                    with self._lock:
                        if resource_name in self._bindings:
                            self._bindings[resource_name].last_error = str(exc)
                            self._bindings[resource_name].status = "error"
                    time.sleep(2.0)
            client.close()
            return True
        except Exception:
            return False

    def _stream_loop_http(
        self, binding: InboundBinding, resource_name: str, remote_url: str
    ) -> None:
        try:
            from palm.providers.palm.events_client import PalmEventsClient

            client = PalmEventsClient(remote_url)
            types = list(binding.spec.event_types) or None
            while not self._worker_stop.is_set():
                try:
                    events = client.poll(types=types, limit=50)
                    for ev in events:
                        if self._worker_stop.is_set():
                            break
                        envelope = {
                            "type": ev.get("type"),
                            "payload": ev.get("payload") or {},
                            "offset": ev.get("offset"),
                            "source": "stream",
                            "transport": "http",
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

    def _poll_loop(self, resource_name: str) -> None:
        binding = self.resolve(resource_name)
        if binding is None:
            return
        interval = (
            binding.spec.debounce_seconds
            if binding.spec.debounce_seconds > 0
            else _DEFAULT_POLL_INTERVAL
        )
        while not self._worker_stop.is_set():
            try:
                envelope = self._poll_once(binding)
                if envelope is not None:
                    self._signal(binding, envelope, source="poll")
                    with self._lock:
                        if resource_name in self._bindings:
                            self._bindings[resource_name].status = "listening"
                            self._bindings[resource_name].last_error = None
            except Exception as exc:
                with self._lock:
                    if resource_name in self._bindings:
                        self._bindings[resource_name].last_error = str(exc)
                        self._bindings[resource_name].status = "error"
            self._worker_stop.wait(interval)

    def _poll_once(self, binding: InboundBinding) -> dict[str, Any] | None:
        url = (binding.spec.url or self._remote_url(binding) or "").strip()
        if url:
            return self._poll_http(url)
        if self._invoke_resource is None:
            raise RuntimeError("poll mode requires url or invoke_resource callback")
        action = _definition_action(binding.definition) or "get"
        params = dict(_definition_params(binding.definition))
        result = self._invoke_resource(
            binding.resource_name,
            action=action,
            params=params or None,
        )
        if not _result_ok(result):
            err = _result_error(result) or "poll invoke failed"
            raise RuntimeError(err)
        return {
            "resource": binding.resource_name,
            "provider": binding.provider,
            "mode": "poll",
            "payload": {"data": _result_data(result)},
            "source": "poll",
        }

    def _poll_http(self, url: str) -> dict[str, Any]:
        req = Request(url, headers={"Accept": "application/json"}, method="GET")
        try:
            with urlopen(req, timeout=15.0) as resp:
                raw = resp.read().decode("utf-8")
        except (HTTPError, URLError, TimeoutError) as exc:
            raise RuntimeError(f"poll GET failed: {exc}") from exc
        try:
            payload = json.loads(raw) if raw.strip() else {}
        except json.JSONDecodeError:
            payload = {"raw": raw}
        if not isinstance(payload, dict):
            payload = {"value": payload}
        return {
            "mode": "poll",
            "payload": payload,
            "source": "poll",
            "url": url,
        }

    def _remote_url(self, binding: InboundBinding) -> str | None:
        if binding.spec.url:
            return binding.spec.url
        params = _definition_params(binding.definition)
        u = params.get("remote_url") or params.get("base_url")
        return str(u) if u else None

    def _check_secret(
        self,
        binding: InboundBinding,
        *,
        headers: dict[str, str],
        provided: str | None,
    ) -> None:
        spec = binding.spec
        expected = None
        params = _definition_params(binding.definition)
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
        self, binding: InboundBinding, body: Any, *, source: str
    ) -> dict[str, Any]:
        if isinstance(body, dict) and "payload" in body and "resource" in body:
            return dict(body)
        if isinstance(body, dict):
            payload = dict(body)
        else:
            payload = {"value": body}
        return {
            "resource": binding.resource_name,
            "provider": binding.provider,
            "mode": binding.spec.mode,
            "payload": payload,
            "source": source,
        }

    def _store_envelope(
        self, binding: InboundBinding, envelope: dict[str, Any]
    ) -> dict[str, Any]:
        """Optional inbox persist via store_resource before WorkIntent (0.44)."""
        spec = binding.spec
        store_name = (spec.store_resource or "").strip()
        if not store_name or self._invoke_resource is None:
            return {}
        detail = self._get_resource(store_name) if self._get_resource else None
        action = (spec.store_action or "").strip() or None
        if not action and isinstance(detail, dict):
            action = _definition_action(detail) or "put"
        action = action or "put"
        base_params = dict(_definition_params(detail)) if isinstance(detail, dict) else {}
        params = {**base_params, "value": envelope}
        try:
            result = self._invoke_resource(store_name, action=action, params=params)
        except Exception as exc:
            return {
                "stored": False,
                "store_resource": store_name,
                "store_error": str(exc),
            }
        if not _result_ok(result):
            return {
                "stored": False,
                "store_resource": store_name,
                "store_error": _result_error(result) or "store invoke failed",
            }
        return {"stored": True, "store_resource": store_name, "store_action": action}

    def _signal(
        self,
        binding: InboundBinding,
        envelope: dict[str, Any],
        *,
        source: str,
    ) -> tuple[str, dict[str, Any]]:
        from datetime import UTC, datetime

        spec = binding.spec
        store_meta = self._store_envelope(binding, envelope)

        if spec.debounce_seconds > 0 and source != "poll":
            key = binding.resource_name
            now = time.monotonic()
            until = self._debounce_until.get(key, 0.0)
            if now < until:
                return "", store_meta
            self._debounce_until[key] = now + spec.debounce_seconds

        coalesce = spec.coalesce_key
        if not coalesce and spec.coalesce_field:
            payload = (
                envelope.get("payload") if isinstance(envelope.get("payload"), dict) else {}
            )
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
                **store_meta,
            },
            coalesce_key=coalesce,
        )
        intent_id = self._enqueue(intent)

        with self._lock:
            b = self._bindings.get(binding.resource_name)
            if b is not None:
                b.signal_count += 1
                b.last_signal_at = datetime.now(UTC).isoformat()
                if source in ("stream", "poll"):
                    b.status = "listening"
                b.last_error = store_meta.get("store_error") or None

        if self._event is not None:
            try:
                self._event.emit(
                    "inbound.received",
                    resource_ref=binding.resource_name,
                    source=source,
                    intent_id=intent_id or None,
                    work_target=target,
                    stored=store_meta.get("stored"),
                    store_resource=store_meta.get("store_resource"),
                )
            except Exception:
                pass
        return intent_id or "", store_meta


def _definition_metadata(detail: dict[str, Any]) -> dict[str, Any]:
    meta = detail.get("metadata")
    if not isinstance(meta, dict):
        meta = (detail.get("resource") or {}).get("metadata") if isinstance(
            detail.get("resource"), dict
        ) else None
    if not isinstance(meta, dict):
        meta = detail.get("metadata") if isinstance(detail.get("metadata"), dict) else {}
    if "inbound" not in (meta or {}):
        inner = detail.get("definition") or detail
        if isinstance(inner, dict) and isinstance(inner.get("metadata"), dict):
            meta = inner["metadata"]
    return meta if isinstance(meta, dict) else {}


def _definition_action(detail: dict[str, Any] | None) -> str | None:
    if not isinstance(detail, dict):
        return None
    action = detail.get("action")
    if action:
        return str(action)
    inner = detail.get("definition")
    if isinstance(inner, dict) and inner.get("action"):
        return str(inner["action"])
    return None


def _definition_params(detail: dict[str, Any] | None) -> dict[str, Any]:
    if not isinstance(detail, dict):
        return {}
    params = detail.get("params")
    if isinstance(params, dict):
        return dict(params)
    inner = detail.get("definition")
    if isinstance(inner, dict) and isinstance(inner.get("params"), dict):
        return dict(inner["params"])
    return {}


def _result_ok(result: Any) -> bool:
    if result is None:
        return False
    if isinstance(result, dict):
        return bool(result.get("success", False))
    return bool(getattr(result, "success", False))


def _result_data(result: Any) -> Any:
    if isinstance(result, dict):
        return result.get("data")
    return getattr(result, "data", None)


def _result_error(result: Any) -> str | None:
    if isinstance(result, dict):
        err = result.get("error")
        return str(err) if err else None
    err = getattr(result, "error", None)
    return str(err) if err else None


__all__ = ["InboundBinding", "InboundBindingService"]