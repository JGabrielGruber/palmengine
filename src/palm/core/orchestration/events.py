"""
Orchestration observability event names.

Published through ``EventEngine`` when wired into ``OrchestrationEngine``.
"""

from __future__ import annotations


class OrchestrationEventType:
    ENGINE_STARTED = "orchestration.started"
    ENGINE_SHUTDOWN = "orchestration.shutdown"
    JOB_SUBMITTED = "job.submitted"
    JOB_STATUS_CHANGED = "job.status_changed"
    JOB_COMPLETED = "job.completed"
    FLOW_SESSION_SUCCEEDED = "flow.session.succeeded"
    FLOW_SESSION_FAILED = "flow.session.failed"
    JOB_INPUT_RECEIVED = "job.input_received"
    JOB_CANCELLED = "job.cancelled"
    INSTANCE_CREATED = "instance.created"
    INSTANCE_STATUS_CHANGED = "instance.status_changed"
