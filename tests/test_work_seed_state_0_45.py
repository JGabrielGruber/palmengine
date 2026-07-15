"""0.45.1 — inbound work.seed_state parse and resolve."""

from __future__ import annotations

from palm.common.resource.inbound import parse_inbound_spec
from palm.common.work.seed_state import resolve_seed_state


def test_parse_inbound_seed_state() -> None:
    spec = parse_inbound_spec(
        {
            "inbound": {
                "enabled": True,
                "mode": "webhook",
                "work": {
                    "flow_id": "react",
                    "seed_state": {
                        "event": "inbound.payload",
                        "source": "source",
                    },
                },
            }
        }
    )
    assert spec is not None
    assert spec.work.seed_state == {"event": "inbound.payload", "source": "source"}


def test_resolve_seed_state_maps_paths() -> None:
    payload = {
        "inbound": {"payload": {"type": "job.completed", "id": "j1"}},
        "source": "stream",
    }
    assert resolve_seed_state(
        {"event": "inbound.payload", "source": "source"},
        payload,
    ) == {
        "event": {"type": "job.completed", "id": "j1"},
        "source": "stream",
    }


def test_resolve_seed_state_dollar_prefix() -> None:
    payload = {"inbound": {"payload": {"ok": True}}}
    assert resolve_seed_state({"event": "$.inbound.payload"}, payload) == {
        "event": {"ok": True},
    }