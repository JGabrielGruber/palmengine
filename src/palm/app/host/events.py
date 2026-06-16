"""
ApplicationHost observability event names.
"""

from __future__ import annotations


class HostEventType:
    STARTED = "host.started"
    SHUTDOWN = "host.shutdown"
    OUTBOX_PROCESSED = "host.outbox.processed"
    RUNTIME_REGISTERED = "host.runtime.registered"