"""MCP tool description helpers — weak-LLM ergonomics for coding agents."""

from __future__ import annotations


def tool_description(
    tool_name: str,
    purpose: str,
    *,
    when: str = "",
    examples: list[str] | None = None,
    notes: str = "",
    use_instead: str = "",
) -> str:
    """Build a consistent MCP tool description for ``call_connected_tool`` clients.

    ``tool_name`` should be the bare Palm tool id (e.g. ``palm_assist``). Grok and
    similar hosts may prefix it (``palm___palm_assist``); the instruction line uses
    the canonical ``palm___`` prefix agents see in connected-tool catalogs.
    """
    connected = tool_name if tool_name.startswith("palm___") else f"palm___{tool_name}"
    lines = [
        f'To use this tool: call_connected_tool(tool_name="{connected}", arguments={{...}}).',
        "",
        purpose.strip(),
    ]
    if when:
        lines.extend(["", when.strip()])
    if use_instead:
        lines.extend(["", use_instead.strip()])
    if notes:
        lines.extend(["", notes.strip()])
    if examples:
        lines.extend(["", "Examples::", ""])
        lines.extend(f"    {ex}" for ex in examples)
    return "\n".join(lines)


__all__ = ["tool_description"]