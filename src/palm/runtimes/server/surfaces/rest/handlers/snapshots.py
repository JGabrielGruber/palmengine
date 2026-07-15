"""Snapshot endpoints — list and inspect durable instance state captures."""

from __future__ import annotations

from typing import TYPE_CHECKING

from palm.common.cqrs.query import GetInstanceSnapshotQuery, ListInstanceSnapshotsQuery
from palm.common.exceptions import InstanceNotFoundError
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.surfaces.pagination import list_envelope
from palm.common.surfaces.serializers import snapshot_detail, snapshot_summary
from palm.runtimes.server.surfaces.rest import errors
from palm.runtimes.server.surfaces.rest.responses import ok
from palm.runtimes.server.surfaces.rest.validation import (
    PaginationParams,
    parse_list_snapshots_query,
)

if TYPE_CHECKING:
    from palm.runtimes.server.context import ServerContext


def list_snapshots(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
) -> ServerResponse:
    query = parse_list_snapshots_query(request)
    if isinstance(query, ServerResponse):
        return query

    try:
        snapshots = ctx.ask(ListInstanceSnapshotsQuery(instance_id=instance_id))
    except InstanceNotFoundError:
        return errors.instance_not_found(instance_id)

    rows = [snapshot_summary(index, snap) for index, snap in enumerate(snapshots)]
    params = PaginationParams(limit=query["limit"], offset=query["offset"])
    return ok(list_envelope("snapshots", rows, params))


def get_snapshot(
    ctx: ServerContext,
    request: ServerRequest,
    *,
    instance_id: str,
    snapshot_id: str,
) -> ServerResponse:
    try:
        resolved = ctx.ask(
            GetInstanceSnapshotQuery(instance_id=instance_id, snapshot_id=snapshot_id)
        )
    except InstanceNotFoundError:
        return errors.instance_not_found(instance_id)

    if resolved is None:
        return errors.snapshot_not_found(instance_id, snapshot_id)

    index, snapshot = resolved
    return ok(snapshot_detail(index, snapshot))
