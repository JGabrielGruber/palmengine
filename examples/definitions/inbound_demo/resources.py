"""Inbound-capable resources — same ResourceDefinition kind as pull resources."""

from __future__ import annotations

import os

from palm.definitions import ResourceDefinition


INBOUND_WEBHOOK_DEMO = ResourceDefinition(
    id="resource-inbound-webhook-demo",
    name="inbound-webhook-demo",
    provider="kv",
    action="put",
    resource_id="inbound/webhook-demo",
    params={"inbound_secret": os.environ.get("PALM_INBOUND_DEMO_SECRET", "")},
    metadata={
        "description": "Webhook ingress dogfood — POST /v1/api/inbound/inbound-webhook-demo",
        "tags": ["inbound", "webhook", "dogfood"],
        "inbound": {
            "enabled": True,
            "mode": "webhook",
            "path": "inbound-webhook-demo",
            "secret_header": "X-Palm-Inbound-Secret",
            "secret_param": "inbound_secret",
            "work": {"kind": "run_flow", "flow_id": "on-inbound-webhook"},
            "coalesce_field": "id",
            "debounce_seconds": 0,
        },
    },
)


def _origin_events() -> ResourceDefinition:
    """Stream inbound from another Palm when PALM_ORIGIN_URL is set."""
    url = (os.environ.get("PALM_ORIGIN_URL") or "").strip()
    return ResourceDefinition(
        id="resource-origin-events-inbound",
        name="origin-events-inbound",
        provider="palm",
        action="list_jobs",  # pull still valid; inbound.stream is extra capability
        resource_id="list_jobs",
        params={"remote_url": url} if url else {},
        metadata={
            "description": "Inbound stream from origin Palm events (set PALM_ORIGIN_URL)",
            "tags": ["inbound", "stream", "palm", "composition"],
            "inbound": {
                "enabled": bool(url),
                "mode": "stream",
                "work": {"kind": "run_flow", "flow_id": "on-inbound-webhook"},
                "event_types": ["resource.changed", "job.completed"],
                "debounce_seconds": 2,
            },
        },
    )


ORIGIN_EVENTS_INBOUND = _origin_events()

__all__ = ["INBOUND_WEBHOOK_DEMO", "ORIGIN_EVENTS_INBOUND"]
