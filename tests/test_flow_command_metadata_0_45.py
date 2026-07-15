"""0.45.1 — flow_command_from_body passes metadata and state."""

from __future__ import annotations

from palm.services.execution.flows import flow_command_from_body


def test_flow_command_from_body_passes_metadata_and_state() -> None:
    cmd = flow_command_from_body(
        {
            "flow_name": "my-flow",
            "metadata": {"inbound": {"id": "e1"}, "source": "webhook"},
            "state": {"event": {"id": "e1"}},
        }
    )
    assert cmd.flow == "my-flow"
    assert cmd.metadata == {"inbound": {"id": "e1"}, "source": "webhook"}
    assert cmd.state == {"event": {"id": "e1"}}


def test_flow_command_from_body_empty_metadata_default() -> None:
    cmd = flow_command_from_body({"flow_name": "x"})
    assert cmd.metadata == {}
    assert cmd.state is None