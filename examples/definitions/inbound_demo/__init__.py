"""Inbound resource dogfood pack (0.43) — resources that listen."""

from __future__ import annotations

from . import flows, resources

__all__ = ["flows", "resources", "register_definitions"]


def register_definitions(repository: object) -> None:
    save_resource = getattr(repository, "save_resource", None)
    save_flow = getattr(repository, "save_flow", None)
    publish_resource = getattr(repository, "publish_resource_revision", None)
    publish_flow = getattr(repository, "publish_flow_revision", None)

    for res in (resources.INBOUND_WEBHOOK_DEMO, resources.ORIGIN_EVENTS_INBOUND):
        if callable(publish_resource):
            publish_resource(res)
        elif callable(save_resource):
            save_resource(res)

    if callable(publish_flow):
        publish_flow(flows.ON_INBOUND_WEBHOOK)
    elif callable(save_flow):
        save_flow(flows.ON_INBOUND_WEBHOOK)
