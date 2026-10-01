"""
Execution-layer hooks — cross-cutting concerns for orchestration jobs.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from palm.common.exceptions import InstanceNotFoundError
from palm.core.exceptions import RegistryError
from palm.core.orchestration.events import OrchestrationEventType
from palm.core.orchestration.hooks import JobHookAdapter
from palm.definitions.flow import FlowDefinition

if TYPE_CHECKING:
    from palm.common.events.outbox import OutboxStore
    from palm.common.events.reliable import ReliableEventPublisher
    from palm.common.managers.instance_manager import InstanceManager
    from palm.common.persistence.instance_repository import InstanceRepository
    from palm.core.orchestration.engine import OrchestrationEngine
    from palm.core.orchestration.job import Job
    from palm.core.orchestration.run_result import RunResult

_log = logging.getLogger(__name__)


class InstancePersistenceHook(JobHookAdapter):
    """
    Track and persist jobs that carry an ``instance_id`` in metadata.

    Creates the instance record on first submit, then updates on status changes.
    Optionally records durable domain events in the outbox after successful writes.
    """

    def __init__(
        self,
        instances: InstanceRepository | InstanceManager,
        *,
        outbox_store: OutboxStore | None = None,
        publisher: ReliableEventPublisher | None = None,
    ) -> None:
        self._instances = instances
        self._outbox_store = outbox_store
        self._publisher = publisher

    def on_job_submitted(self, engine: OrchestrationEngine, job: Job) -> None:
        created = self._ensure_instance(job)
        if created:
            self._publish_instance_event(
                OrchestrationEventType.INSTANCE_CREATED,
                job,
                status=job.status.value,
            )

    def on_job_status_changed(
        self,
        engine: OrchestrationEngine,
        job: Job,
        result: RunResult | None = None,
    ) -> None:
        updated = self._ensure_instance(job)
        if updated:
            self._publish_instance_event(
                OrchestrationEventType.INSTANCE_STATUS_CHANGED,
                job,
                status=job.status.value,
            )

    def _ensure_instance(self, job: Job) -> bool:
        iid = job.metadata.get("instance_id")
        if not iid:
            return False
        try:
            self._instances.get(str(iid))
            self._instances.update(job, instance_id=str(iid))
            return True
        except InstanceNotFoundError:
            flow_def = job.metadata.get("flow_definition")
            if not isinstance(flow_def, dict):
                return False
            try:
                flow = FlowDefinition.from_dict(flow_def)
            except (TypeError, ValueError, KeyError) as exc:
                # Documented ignore: bad embedded flow_definition (CS-005).
                _log.debug(
                    "instance create skipped: flow_definition invalid instance_id=%s: %s",
                    iid,
                    exc,
                )
                return False
            try:
                self._instances.create(
                    job,
                    flow=flow,
                    instance_id=str(iid),
                    process_id=job.metadata.get("process_id"),
                    process_name=job.metadata.get("process"),
                )
                return True
            except RegistryError:
                raise
            except Exception:
                # Documented ignore: persistence must not fail job lifecycle (CS-005).
                _log.exception(
                    "instance create failed instance_id=%s job_id=%s",
                    iid,
                    getattr(job, "id", None),
                )
                return False
        except RegistryError:
            raise
        except Exception:
            # Documented ignore: update path best-effort (CS-005).
            _log.exception(
                "instance update failed instance_id=%s job_id=%s",
                iid,
                getattr(job, "id", None),
            )
            return False

    def _publish_instance_event(
        self,
        event_type: str,
        job: Job,
        *,
        status: str,
    ) -> None:
        from palm.common.events.reliable import event_context_from_job
        from palm.core.event import Event

        iid = job.metadata.get("instance_id")
        if iid is None:
            return
        payload: dict[str, object] = {
            "instance_id": str(iid),
            "job_id": job.id,
            "status": status,
        }
        sid = job.metadata.get("session_id")
        if sid is not None and str(sid).strip():
            payload["session_id"] = str(sid).strip()
        event = Event(
            type=event_type,
            payload=payload,
            context=event_context_from_job(job),
        )
        try:
            if self._publisher is not None:
                self._publisher.enqueue(event)
            elif self._outbox_store is not None:
                self._outbox_store.enqueue(event)
        except Exception:
            # Documented ignore: outbox publish must not fail job lifecycle (CS-005).
            _log.exception(
                "instance event enqueue failed type=%s instance_id=%s",
                event_type,
                iid,
            )
            return None
