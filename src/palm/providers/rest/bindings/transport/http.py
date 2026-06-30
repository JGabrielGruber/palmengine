"""HTTP client for REST provider invocations."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from typing import Any

from palm.providers.rest.exceptions import RestRemoteError

_TRANSIENT_STATUS = frozenset({429, 502, 503, 504})


def http_request(
    method: str,
    url: str,
    *,
    headers: dict[str, str] | None = None,
    timeout: float = 10.0,
    retries: int = 2,
) -> tuple[int, Any]:
    """Execute an HTTP request with basic retry for transient failures."""
    attempts = max(retries, 0) + 1
    delay = 0.05
    last_error: RestRemoteError | None = None
    req_headers = {"Accept": "application/json", **(headers or {})}

    for attempt in range(attempts):
        try:
            req = urllib.request.Request(
                url,
                headers=req_headers,
                method=method.upper(),
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
                if "application/json" in resp.headers.get("Content-Type", ""):
                    parsed = json.loads(raw)
                    return resp.status, parsed
                return resp.status, raw
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8")
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"error": raw}
            if exc.code in _TRANSIENT_STATUS and attempt < attempts - 1:
                time.sleep(delay)
                delay = min(delay * 2, 0.5)
                continue
            raise RestRemoteError(
                f"HTTP {exc.code} for {method.upper()} {url}: {parsed}",
                status_code=exc.code,
                payload=parsed,
                transient=exc.code in _TRANSIENT_STATUS,
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = RestRemoteError(
                f"Transport error for {method.upper()} {url}: {exc}",
                transient=True,
            )
            if attempt >= attempts - 1:
                raise last_error from exc
            time.sleep(delay)
            delay = min(delay * 2, 0.5)

    if last_error is not None:
        raise last_error
    raise RestRemoteError(f"HTTP request failed for {method.upper()} {url}")
