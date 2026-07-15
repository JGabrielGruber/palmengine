"""
System event watchdog — internal inbound → pipeline → kv log (0.45.3).

Loop guards:
  - ``event_types`` excludes ``resource.changed`` and ``inbound.received`` (put/inbox
    would re-trigger forever).
  - Pipeline ``conditional`` + ``passthrough`` drops rows for owned resources and this
    flow's own completions.
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition, ResourceDefinition

_NS = "palm"
_BACKEND = "auto"

_WATCH_FLOW = "palm-system-watch-event"
_OWNED_RESOURCE_REFS = (
    "palm-system-event-log",
    "palm-system-event-inbox",
    "palm-system-events-watch",
)


def _exclude_row_steps() -> list[dict[str, object]]:
    steps: list[dict[str, object]] = []
    for ref in _OWNED_RESOURCE_REFS:
        steps.append(
            {
                "name": f"exclude_{ref.replace('-', '_')}",
                "source_key": "row",
                "target_key": "row",
                "rule": "conditional",
                "options": {
                    "field": "resource_ref",
                    "not_equals": ref,
                    "passthrough": True,
                    "else": None,
                },
                "skip_if_missing": True,
            }
        )
    return steps


PALM_SYSTEM_EVENT_INBOX = ResourceDefinition(
    id="resource-palm-system-event-inbox",
    name="palm-system-event-inbox",
    provider="kv",
    action="put",
    resource_id="system/event-inbox",
    params={"namespace": _NS, "backend": _BACKEND},
    metadata={
        "description": "Inbound audit snapshot (store_resource target; not published)",
        "tags": ["palm", "system", "ops", "inbound", "audit"],
    },
)

PALM_SYSTEM_EVENT_LOG = ResourceDefinition(
    id="resource-palm-system-event-log",
    name="palm-system-event-log",
    provider="kv",
    action="get",
    resource_id="system/event-log",
    params={
        "namespace": _NS,
        "backend": _BACKEND,
        "default": [],
    },
    metadata={
        "description": "System event tail (pipeline append; analytics table)",
        "tags": ["palm", "system", "ops", "watchdog", "bi"],
        "analytics": {
            "published": True,
            "kind": "fact",
            "default_profile": "table",
            "row_path": "value",
        },
    },
)

PALM_SYSTEM_EVENTS_WATCH = ResourceDefinition(
    id="resource-palm-system-events-watch",
    name="palm-system-events-watch",
    provider="palm",
    action="get",
    resource_id="system/events-watch",
    params={},
    metadata={
        "description": "In-process event watch (internal inbound; no loopback)",
        "tags": ["palm", "system", "ops", "inbound", "watchdog"],
        "inbound": {
            "enabled": True,
            "mode": "internal",
            "skip_self": True,
            "event_types": ["job.completed", "flow.session.succeeded"],
            "store_resource": "palm-system-event-inbox",
            "store_action": "put",
            "debounce_seconds": 0,
            "work": {
                "flow_id": _WATCH_FLOW,
                "coalesce_key": "palm-system-events-watch",
                "seed_state": {
                    "event": "inbound.payload",
                    "etype": "inbound.type",
                    "event_id": "inbound.event_id",
                },
            },
        },
    },
)

PALM_SYSTEM_WATCH_EVENT_FLOW = FlowDefinition(
    id="flow-palm-system-watch-event",
    name=_WATCH_FLOW,
    pattern="pipeline",
    options={
        "initial_state": {"probe": {"load": True}},
        "steps": [
            {
                "name": "load_log",
                "source_key": "probe",
                "target_key": "events",
                "rule": "enrich_resource",
                "options": {
                    "resource_ref": "palm-system-event-log",
                    "action": "get",
                    "merge": False,
                },
            },
            {
                "name": "unwrap_log",
                "source_key": "events",
                "target_key": "events",
                "rule": "jsonpath_extract",
                "options": {"path": "value", "default": []},
            },
            {
                "name": "stamp_row",
                "source_key": "event",
                "target_key": "row",
                "rule": "jsonpath_set",
                "options": {"path": "type", "set_value_from_key": "etype"},
                "skip_if_missing": True,
            },
            {
                "name": "attach_event_id",
                "source_key": "row",
                "target_key": "row",
                "rule": "jsonpath_set",
                "options": {"path": "event_id", "set_value_from_key": "event_id"},
                "skip_if_missing": True,
            },
            {
                "name": "exclude_self_flow",
                "source_key": "row",
                "target_key": "row",
                "rule": "conditional",
                "options": {
                    "field": "flow",
                    "not_equals": _WATCH_FLOW,
                    "passthrough": True,
                    "else": None,
                },
                "skip_if_missing": True,
            },
            {
                "name": "exclude_self_flow_name",
                "source_key": "row",
                "target_key": "row",
                "rule": "conditional",
                "options": {
                    "field": "flow_name",
                    "not_equals": _WATCH_FLOW,
                    "passthrough": True,
                    "else": None,
                },
                "skip_if_missing": True,
            },
            *_exclude_row_steps(),
            {
                "name": "append_event",
                "source_key": "row",
                "target_key": "events",
                "rule": "append_item",
                "options": {"max_items": 50, "unique_field": "event_id", "prepend": True},
                "skip_if_missing": True,
            },
            {
                "name": "persist_log",
                "source_key": "events",
                "target_key": "events",
                "rule": "put_resource",
                "options": {
                    "resource": "palm-system-event-log",
                    "action": "put",
                },
            },
        ],
    },
)

PALM_SYSTEM_WATCH_EVENT_PROCESS = ProcessDefinition(
    id="proc-palm-system-watch-event",
    name=_WATCH_FLOW,
    flows=[PALM_SYSTEM_WATCH_EVENT_FLOW],
    metadata={
        "example": True,
        "description": "System event watchdog process (internal inbound)",
    },
)


def register_definitions(repository: object) -> None:
    save = getattr(repository, "save_resource", None)
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    for res in (
        PALM_SYSTEM_EVENT_INBOX,
        PALM_SYSTEM_EVENT_LOG,
        PALM_SYSTEM_EVENTS_WATCH,
    ):
        if callable(save):
            save(res)
    if callable(save_flow):
        save_flow(PALM_SYSTEM_WATCH_EVENT_FLOW)
    if callable(save_process):
        save_process(PALM_SYSTEM_WATCH_EVENT_PROCESS)


__all__ = [
    "PALM_SYSTEM_EVENT_INBOX",
    "PALM_SYSTEM_EVENT_LOG",
    "PALM_SYSTEM_EVENTS_WATCH",
    "PALM_SYSTEM_WATCH_EVENT_FLOW",
    "PALM_SYSTEM_WATCH_EVENT_PROCESS",
    "_OWNED_RESOURCE_REFS",
    "_WATCH_FLOW",
    "register_definitions",
]