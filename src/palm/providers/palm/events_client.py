"""Palm provider event consumer — journal poll over HTTP (0.42).

WS live subscribe is available at ``/ws/v1/events``; this client uses the
**HTTP journal** for catch-up and simple composition (works with any HTTP stack).
"""

from __future__ import annotations

from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json


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


__all__ = ["PalmEventsClient"]
