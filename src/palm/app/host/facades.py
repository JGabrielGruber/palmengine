"""
Host read facades (0.50.4) — cohesive, navigable groupings of the host's queries.

``host.instances`` / ``host.jobs`` / ``host.wizards`` gather the flat
``list_instance_views``/``get_wizard_progress``/… query methods into sub-objects —
the *capability surface* a ``CompositionProfile`` will (later) turn on/off per shape.

Additive: the host keeps the flat methods as thin delegators, so nothing breaks;
they are the "dead leaves" a later season may prune. Each facade is a thin shell over
the host's query bus (``host.ask``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.cqrs.query import (
    GetInstanceStatusQuery,
    ListInstanceSnapshotsQuery,
    ListInstancesQuery,
    ListJobStatusQuery,
)
from palm.patterns.wizard.bindings.cqrs.queries import (
    GetWizardProgressQuery,
    ListWizardProgressQuery,
)

if TYPE_CHECKING:
    from palm.app.host.application_host import ApplicationHost
    from palm.common.cqrs.projections.instance_index import InstanceReadModel
    from palm.common.cqrs.projections.job_status_board import JobStatusReadModel
    from palm.patterns.wizard.bindings.cqrs.projection import WizardProgressReadModel


class InstancesFacade:
    """Read side for process instances — ``host.instances``."""

    def __init__(self, host: ApplicationHost) -> None:
        self._host = host

    def list(
        self,
        *,
        status: str | None = None,
        flow_name: str | None = None,
        include_terminal: bool = True,
        limit: int | None = None,
    ) -> list[InstanceReadModel]:
        return self._host.ask(
            ListInstancesQuery(
                status=status,
                flow_name=flow_name,
                include_terminal=include_terminal,
                limit=limit,
            )
        )

    def get(self, instance_id: str) -> InstanceReadModel | None:
        return self._host.ask(GetInstanceStatusQuery(instance_id=instance_id))

    def snapshots(self, instance_id: str) -> list:
        return self._host.ask(ListInstanceSnapshotsQuery(instance_id=instance_id))


class JobsFacade:
    """Read side for jobs — ``host.jobs``."""

    def __init__(self, host: ApplicationHost) -> None:
        self._host = host

    def list(
        self,
        *,
        status: str | None = None,
        limit: int | None = None,
    ) -> list[JobStatusReadModel]:
        return self._host.ask(ListJobStatusQuery(status=status, limit=limit))


class WizardsFacade:
    """Read side for wizard progress — ``host.wizards``."""

    def __init__(self, host: ApplicationHost) -> None:
        self._host = host

    def progress(
        self,
        *,
        instance_id: str | None = None,
        job_id: str | None = None,
    ) -> WizardProgressReadModel | None:
        return self._host.ask(GetWizardProgressQuery(instance_id=instance_id, job_id=job_id))

    def list(
        self,
        *,
        limit: int | None = 10,
        active_only: bool = False,
    ) -> list[WizardProgressReadModel]:
        return self._host.ask(ListWizardProgressQuery(limit=limit, active_only=active_only))


__all__ = ["InstancesFacade", "JobsFacade", "WizardsFacade"]
