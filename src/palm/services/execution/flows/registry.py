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
        "session_context",
        ("flows", "{flow_id}", "session", "{session_id}"),
        "Inspect session context",
    ),
    CommandSpec(
        "session_input",
        ("flows", "{flow_id}", "session", "{session_id}", "input"),
        "Provide interactive input",
    ),
    CommandSpec(
        "session_backtrack",
        ("flows", "{flow_id}", "session", "{session_id}", "backtrack"),
        "Backtrack to a prior step",
    ),
    CommandSpec(
        "session_resume",
        ("flows", "{flow_id}", "session", "{session_id}", "resume"),
        "Resume a waiting interactive flow",
    ),
    CommandSpec(
        "session_resume_child_wait",
        ("flows", "{flow_id}", "session", "{session_id}", "resume-child-wait"),
        "Resume after nested child wait",
    ),
    CommandSpec(
        "session_cancel",
        ("flows", "{flow_id}", "session", "{session_id}", "cancel"),
        "Cancel the session job",
    ),
]


def flow_commands() -> tuple[CommandSpec, ...]:
    return tuple(_registry)


__all__ = ["CommandSpec", "flow_commands"]