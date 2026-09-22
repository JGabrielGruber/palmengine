"""
ApplicationHost observability event names.
"""

from __future__ import annotations


class HostEventType:
    STARTED = "host.started"
    SHUTDOWN = "host.shutdown"
    RECOVERED = "host.recovered"
    RUNTIME_REGISTERED = "host.runtime.registered"
    COMMAND_DISPATCHED = "host.command.dispatched"
    WORKERS_READY = "host.workers.ready"
