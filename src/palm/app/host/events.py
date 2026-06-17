"""
ApplicationHost observability event names.
"""

from __future__ import annotations


class HostEventType:
    STARTED = "host.started"
    SHUTDOWN = "host.shutdown"
    RECOVERED = "host.recovered"
    OUTBOX_PROCESSED = "host.outbox.processed"
    RUNTIME_REGISTERED = "host.runtime.registered"
    COMMAND_DISPATCHED = "host.command.dispatched"
    WORKERS_READY = "host.workers.ready"
    WEBHOOK_DELIVERED = "host.webhook.delivered"
    WEBHOOK_FAILED = "host.webhook.failed"
