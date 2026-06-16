"""
REPL auto-completion — definitions, instances, and command phrases.
"""

from __future__ import annotations

from typing import Any

from palm.runtimes.cli.commands.registry import CommandRegistry
from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.shared.instance_ops import is_terminal_status


def build_repl_completer(
    ctx: CliContext,
    registry: CommandRegistry,
    *,
    completer_cls: Any,
    completion_cls: Any,
) -> Any:
    phrases = sorted(registry.handlers.keys(), key=len)
    tokens = sorted({phrase.split()[0] for phrase in phrases})

    class PalmCompleter(completer_cls):  # type: ignore[misc]
        def get_completions(self, document: Any, complete_event: Any) -> Any:
            text = document.text_before_cursor
            stripped = text.strip()
            words = stripped.split()
            lower_words = [word.lower() for word in words]

            if not words:
                for token in tokens:
                    yield completion_cls(token)
                return

            if len(words) == 1:
                prefix = lower_words[0]
                for token in tokens:
                    if token.startswith(prefix):
                        yield completion_cls(token, start_position=-len(words[0]))
                for phrase in phrases:
                    if phrase.startswith(prefix):
                        yield completion_cls(phrase, start_position=-len(words[0]))
                return

            phrase = " ".join(lower_words[: min(3, len(lower_words))])
            for candidate in phrases:
                if candidate.startswith(phrase) and candidate != phrase:
                    yield completion_cls(
                        candidate,
                        start_position=-len(" ".join(words[: min(3, len(words))])),
                    )

            yield from _context_completions(
                ctx,
                words,
                completion_cls,
            )

    return PalmCompleter()


def _context_completions(
    ctx: CliContext,
    words: list[str],
    completion_cls: Any,
) -> Any:
    lower = [word.lower() for word in words]
    include_all = "--all" in lower

    flow_start_phrases = (
        ("flow", "start"),
        ("start",),
        ("wizard", "start"),
    )
    for pattern in flow_start_phrases:
        if _matches_phrase(lower, pattern) and len(words) > len(pattern):
            yield from _complete_prefix(words[-1], _flow_names(ctx), completion_cls)
            return

    if _matches_phrase(lower, ("process", "submit")) and len(words) >= 3:
        yield from _complete_prefix(words[-1], _process_names(ctx), completion_cls)
        return

    if _matches_phrase(lower, ("instance", "snapshots")) and len(words) >= 2:
        partial = words[-1] if len(words) > 2 else ""
        yield from _complete_prefix(
            partial,
            _instance_refs(ctx, include_all=True, snapshots_only=True),
            completion_cls,
        )
        return

    if _matches_phrase(lower, ("status",)) and len(words) == 1:
        for flag in ("--dashboard", "--brief", "--full"):
            if flag.startswith(words[-1]):
                yield completion_cls(flag, start_position=-len(words[-1]))
        return

    if _matches_phrase(lower, ("doctor",)) and len(words) == 1:
        if "--dashboard".startswith(words[-1]):
            yield completion_cls("--dashboard", start_position=-len(words[-1]))
        return

    instance_phrases = (
        ("status",),
        ("instance", "status"),
        ("instance", "resume"),
        ("process", "resume"),
        ("input",),
        ("back",),
        ("wizard", "status"),
        ("wizard", "input"),
    )
    for pattern in instance_phrases:
        if _matches_phrase(lower, pattern) and len(words) > len(pattern):
            partial = words[-1]
            yield from _complete_prefix(
                partial,
                _instance_refs(ctx, include_all=include_all),
                completion_cls,
            )
            return

    if _matches_phrase(lower, ("instance", "list")):
        if words[-1].startswith("--") and words[-1] not in (
            "--status",
            "--flow",
            "--limit",
            "--format",
        ):
            for flag in ("--all", "--status", "--flow", "--limit", "--format"):
                if flag.startswith(words[-1]):
                    yield completion_cls(flag, start_position=-len(words[-1]))
            return
        if "--flow" in lower:
            flow_index = lower.index("--flow")
            if len(words) > flow_index + 1 and words[-1] == words[flow_index + 1]:
                yield from _complete_prefix(words[-1], _flow_names(ctx), completion_cls)
            return
        for flag in ("--all", "--status", "--flow", "--limit", "--format"):
            if flag.startswith(words[-1]):
                yield completion_cls(flag, start_position=-len(words[-1]))


def _matches_phrase(words: list[str], pattern: tuple[str, ...]) -> bool:
    if len(words) < len(pattern):
        return False
    return tuple(words[: len(pattern)]) == pattern


def _complete_prefix(partial: str, candidates: list[str], completion_cls: Any) -> Any:
    needle = partial.lower()
    seen: set[str] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        if candidate.lower().startswith(needle):
            seen.add(candidate)
            yield completion_cls(candidate, start_position=-len(partial))


def _instance_refs(
    ctx: CliContext,
    *,
    include_all: bool,
    snapshots_only: bool = False,
) -> list[str]:
    refs: list[str] = []
    for summary in ctx.list_instance_summaries():
        if snapshots_only and summary.snapshot_count <= 0:
            continue
        if not include_all and is_terminal_status(summary.status):
            continue
        refs.append(summary.instance_id)
        short = summary.instance_id[:12]
        if short not in refs:
            refs.append(short)
    if ctx.active_instance_id and ctx.active_instance_id not in refs:
        if not snapshots_only or _active_has_snapshots(ctx):
            refs.insert(0, ctx.active_instance_id)
    return refs


def _active_has_snapshots(ctx: CliContext) -> bool:
    if not ctx.active_instance_id:
        return False
    for summary in ctx.list_instance_summaries():
        if summary.instance_id == ctx.active_instance_id:
            return summary.snapshot_count > 0
    return False


def _flow_names(ctx: CliContext) -> list[str]:
    names: list[str] = []
    for flow in ctx.app.list_flows():
        names.append(flow.name)
    return names


def _process_names(ctx: CliContext) -> list[str]:
    return [process.name for process in ctx.app.list_processes()]
