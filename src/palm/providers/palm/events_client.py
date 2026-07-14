"""Palm provider event consumer — journal poll over HTTP (0.42).

WS live subscribe is at ``/ws/v1/events``. This client uses the **HTTP journal**
for catch-up and composition waits (works with any HTTP stack).
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# Events that mean a job/session may be terminal or progress-worthy for waiters.
_JOB_TERMINAL_TYPES = (
    "job.completed",
    "job.status_changed",
    "flow.session.succeeded",
    "flow.session.failed",
)


class PalmEventsClient:
    """Poll ``GET /v1/api/events/journal`` on a remote (or local) Palm."""

    def __init__(
        self,
        base_url: str,
        *,
        token: str | None = None,
        timeout: float = 30.0,
        subject: str = "dev",
    ) -> None:
        self.base_url = str(base_url).rstrip("/")
        self.token = token
        self.timeout = timeout
        self.subject = subject
        self._offset = 0

    @property
    def offset(self) -> int:
        return self._offset

    def reset(self, offset: int = 0) -> None:
        self._offset = max(0, int(offset))

    def poll(
        self,
        *,
        types: list[str] | None = None,
        limit: int = 100,
        advance: bool = True,
    ) -> list[dict[str, Any]]:
        """Return new public events after current offset."""
        q: dict[str, Any] = {"after": self._offset, "limit": limit}
        if types:
            q["types"] = ",".join(types)
        url = f"{self.base_url}/v1/api/events/journal?{urlencode(q)}"
        headers = {
            "Accept": "application/json",
            "X-Palm-Subject": self.subject,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = Request(url, headers=headers, method="GET")
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"events journal poll failed: {exc}") from exc
        data = body.get("data") if isinstance(body.get("data"), dict) else body
        events = list(data.get("events") or [])
        if advance and events:
            last = events[-1].get("offset")
            if last is not None:
                self._offset = max(self._offset, int(last))
        return events

    def catalog(self) -> dict[str, Any]:
        url = f"{self.base_url}/v1/api/events/catalog"
        req = Request(url, headers={"Accept": "application/json"}, method="GET")
        with urlopen(req, timeout=self.timeout) as resp:
            body = json.loads(resp.read().decode("utf-8"))
        return body.get("data") if isinstance(body.get("data"), dict) else body

    def wait_for(
        self,
        predicate: Callable[[dict[str, Any]], bool],
        *,
        types: list[str] | None = None,
        timeout: float = 30.0,
        poll_interval: float = 0.1,
        limit: int = 100,
    ) -> dict[str, Any]:
        """
        Poll until an event matches *predicate* or *timeout*.

        Returns the matching event dict. Raises ``TimeoutError`` if none.
        """
        deadline = time.monotonic() + max(0.01, float(timeout))
        while time.monotonic() < deadline:
            for ev in self.poll(types=types, limit=limit, advance=True):
                if predicate(ev):
                    return ev
            time.sleep(max(0.01, float(poll_interval)))
        raise TimeoutError(
            f"no matching event within {timeout}s (offset={self._offset})"
        )

    def wait_for_job(
        self,
        job_id: str,
        *,
        timeout: float = 30.0,
        poll_interval: float = 0.1,
        terminal_only: bool = True,
    ) -> dict[str, Any]:
        """Wait for a journal event that references *job_id* (composition helper)."""
        jid = str(job_id or "").strip()
        if not jid:
            raise ValueError("job_id required")

        def _match(ev: dict[str, Any]) -> bool:
            et = str(ev.get("type") or "")
            if terminal_only and et not in _JOB_TERMINAL_TYPES and et != "job.status_changed":
                # still allow job.status_changed when not only terminal types listed
                if et not in _JOB_TERMINAL_TYPES:
                    return False
            payload = ev.get("payload") if isinstance(ev.get("payload"), dict) else {}
            candidates = (
                payload.get("job_id"),
                payload.get("id"),
                (payload.get("job") or {}).get("job_id")
                if isinstance(payload.get("job"), dict)
                else None,
            )
            return jid in {str(c) for c in candidates if c is not None}

        types = list(_JOB_TERMINAL_TYPES)
        return self.wait_for(
            _match,
            types=types,
            timeout=timeout,
            poll_interval=poll_interval,
        )

    def wait_for_resource(
        self,
        resource_ref: str,
        *,
        action: str | None = None,
        timeout: float = 30.0,
        poll_interval: float = 0.1,
    ) -> dict[str, Any]:
        """Wait for ``resource.changed`` matching *resource_ref* (and optional action)."""
        ref = str(resource_ref or "").strip()
        if not ref:
            raise ValueError("resource_ref required")
        act = str(action or "").strip().lower() or None

        def _match(ev: dict[str, Any]) -> bool:
            if str(ev.get("type") or "") != "resource.changed":
                return False
            payload = ev.get("payload") if isinstance(ev.get("payload"), dict) else {}
            r = str(
                payload.get("resource_ref")
                or payload.get("definition_name")
                or ""
            )
            if r != ref and str(payload.get("definition_name") or "") != ref:
                return False
            if act is not None:
                return str(payload.get("action") or "").lower() == act
            return True

        return self.wait_for(
            _match,
            types=["resource.changed"],
            timeout=timeout,
            poll_interval=poll_interval,
        )


def event_mentions_job(event: dict[str, Any], job_id: str) -> bool:
    """True if *event* payload appears to reference *job_id*."""
    jid = str(job_id)
    payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
    for key in ("job_id", "id"):
        if str(payload.get(key) or "") == jid:
            return True
    job = payload.get("job")
    if isinstance(job, dict) and str(job.get("job_id") or "") == jid:
        return True
    return False


__all__ = ["PalmEventsClient", "event_mentions_job"]
