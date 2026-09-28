"""Flow execution contract — REPL command-path specs (transport-agnostic)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandSpec:
    """Declarative flow command path owned by the flows execution domain."""

    command_id: str
    path_pattern: tuple[str, ...]
    summary: str = ""


_registry: list[CommandSpec] = [
    CommandSpec("list_flows", ("flows",), "List runnable flows"),
    CommandSpec("describe_flow", ("flows", "{flow_id}"), "Describe one flow"),
    CommandSpec("create_session", ("flows", "{flow_id}", "create"), "Start a flow session"),
    CommandSpec(
        "instance_context",
        ("flows", "{flow_id}", "instance", "{instance_id}"),
        "Inspect flow instance context",
    ),
    CommandSpec(
        "instance_input",
        ("flows", "{flow_id}", "instance", "{instance_id}", "input"),
        "Provide interactive input",
    ),
    CommandSpec(
        "instance_backtrack",
        ("flows", "{flow_id}", "instance", "{instance_id}", "backtrack"),
        "Backtrack to a prior step",
    ),
    CommandSpec(
        "instance_resume",
        ("flows", "{flow_id}", "instance", "{instance_id}", "resume"),
        "Resume a waiting interactive flow",
    ),
    CommandSpec(
        "instance_cancel",
        ("flows", "{flow_id}", "instance", "{instance_id}", "cancel"),
        "Cancel the instance job",
    ),
]


def flow_commands() -> tuple[CommandSpec, ...]:
    return tuple(_registry)


__all__ = ["CommandSpec", "flow_commands"]