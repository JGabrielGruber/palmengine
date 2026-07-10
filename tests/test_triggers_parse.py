"""0.37 — trigger parse + registry match."""

from __future__ import annotations

from palm.common.triggers import TriggerRegistry, parse_triggers
from palm.core.work import WorkIntent


def test_parse_on_resource() -> None:
    specs = parse_triggers(
        {
            "triggers": [
                {
                    "kind": "on_resource",
                    "resource": "palm-todos",
                    "actions": ["put"],
                    "work": {"flow_id": "todo-analytics"},
                }
            ]
        }
    )
    assert len(specs) == 1
    assert specs[0].kind == "on_resource"
    assert specs[0].work_flow_id == "todo-analytics"


def test_registry_on_resource_event() -> None:
    reg = TriggerRegistry()
    reg.reload_from_flow_rows(
        [
            {
                "name": "watcher",
                "metadata": {
                    "triggers": [
                        {
                            "kind": "on_resource",
                            "resource": "palm-todos",
                            "actions": ["put"],
                            "work": {"flow_id": "todo-analytics"},
                        }
                    ]
                },
            }
        ]
    )
    intents = reg.on_event(
        "resource.changed",
        {"resource_ref": "palm-todos", "action": "put"},
    )
    assert len(intents) == 1
    assert intents[0].target == "todo-analytics"
    assert isinstance(intents[0], WorkIntent)


def test_schedule_interval() -> None:
    reg = TriggerRegistry()
    reg.reload_from_flow_rows(
        [
            {
                "name": "nightly",
                "metadata": {
                    "triggers": [
                        {
                            "kind": "schedule",
                            "interval_seconds": 1,
                            "work": {"flow_id": "todo-analytics"},
                        }
                    ]
                },
            }
        ]
    )
    first = reg.due_schedules(now_ts=100.0)
    assert len(first) == 1
    second = reg.due_schedules(now_ts=100.5)
    assert second == []
    third = reg.due_schedules(now_ts=101.1)
    assert len(third) == 1
