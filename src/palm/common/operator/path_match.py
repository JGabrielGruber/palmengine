"""Match concrete command paths against registry path patterns."""

from __future__ import annotations


def match_command_path(
    segments: list[str] | tuple[str, ...],
    pattern: tuple[str, ...],
) -> dict[str, str] | None:
    """Return captured placeholder values when ``segments`` matches ``pattern``."""
    normalized = tuple(str(segment) for segment in segments)
    if len(normalized) != len(pattern):
        return None
    capture: dict[str, str] = {}
    for segment, token in zip(normalized, pattern, strict=True):
        text = str(token)
        if text.startswith("{") and text.endswith("}"):
            capture[text[1:-1]] = segment
            continue
        if segment != text:
            return None
    return capture


__all__ = ["match_command_path"]