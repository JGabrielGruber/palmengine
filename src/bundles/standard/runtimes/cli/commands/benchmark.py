"""
CLI present for vitality benchmark (0.61.11+).

Law: thrash + metrics live in ``palm.system.vitality``; product door is
``InspectService.benchmark``; this module only parses args and renders.

Human table view uses Linux-style readable units (MiB, ms) by default;
``--json`` / ``--raw`` keep machine numbers.
"""

from __future__ import annotations

from typing import Any

from bundles.standard.runtimes.cli.shared.context import CliContext
from bundles.standard.runtimes.cli.shared.humanize import (
    human_delta,
    human_duration_ms,
    human_metric_value,
)
from bundles.standard.runtimes.cli.shared.output import emit_json
from palm.system.vitality import (
    DEFAULT_ITERATIONS,
    DEFAULT_RECIPE,
    KNOWN_RECIPES,
)


def _parse_args(args: list[str]) -> dict[str, Any]:
    recipe = DEFAULT_RECIPE
    iterations = DEFAULT_ITERATIONS
    store_full = False
    as_json = False
    raw = False
    i = 0
    while i < len(args):
        tok = args[i]
        if tok in {"--recipe", "-r"} and i + 1 < len(args):
            recipe = str(args[i + 1]).strip().lower()
            i += 2
            continue
        if tok in {"-n", "--iterations"} and i + 1 < len(args):
            try:
                iterations = int(args[i + 1])
            except ValueError:
                iterations = DEFAULT_ITERATIONS
            i += 2
            continue
        if tok in {"--full", "--store-full"}:
            store_full = True
            i += 1
            continue
        if tok == "--format" and i + 1 < len(args):
            as_json = str(args[i + 1]).strip().lower() == "json"
            i += 2
            continue
        if tok == "--json":
            as_json = True
            i += 1
            continue
        if tok == "--raw":
            # Machine numbers in table (default is human-readable units).
            raw = True
            i += 1
            continue
        if tok in {"--help", "-h"}:
            return {"help": True}
        # bare recipe name: ``benchmark pulse``
        if not tok.startswith("-") and tok.lower() in KNOWN_RECIPES:
            recipe = tok.lower()
            i += 1
            continue
        i += 1
    return {
        "recipe": recipe,
        "iterations": iterations,
        "store_full": store_full,
        "as_json": as_json,
        "raw": raw,
    }


def cmd_benchmark(ctx: CliContext, args: list[str]) -> int:
    """Run vitality benchmark via host.inspect and present results."""
    opts = _parse_args(args)
    if opts.get("help"):
        recipes = " · ".join(sorted(KNOWN_RECIPES))
        ctx.console.print(
            "[bold]benchmark[/] — vitality load tool (opt-in; Inspect present)\n"
            "  benchmark [recipe] [-n N] [--json] [--raw] [--full]\n"
            "  benchmark work_cycle -n 20\n"
            "  benchmark log_fill -n 25\n"
            f"[dim]recipes:[/] {recipes}\n"
            "[dim]default recipe work_cycle (real work plane). "
            "Human units by default; --raw for plain numbers; --json machine body.[/]"
        )
        return 0

    if ctx.output_format == "json":
        opts["as_json"] = True

    inspect = getattr(ctx.host, "inspect", None)
    if inspect is None:
        ctx.console.print("[red]host.inspect not available[/]")
        return 1
    try:
        runtime = ctx.host.runtime()
    except Exception as exc:
        ctx.console.print(f"[red]runtime not ready:[/] {exc}")
        return 1

    recipe = str(opts.get("recipe") or DEFAULT_RECIPE)
    iterations = int(opts.get("iterations") or DEFAULT_ITERATIONS)
    store_full = bool(opts.get("store_full"))

    try:
        report = inspect.benchmark(
            runtime,
            recipe=recipe,
            iterations=iterations,
            store_full_snapshots=store_full,
        )
    except Exception as exc:
        ctx.console.print(f"[red]benchmark failed:[/] {exc}")
        return 1

    if opts.get("as_json"):
        emit_json(ctx.console, report)
        return 0 if report.get("state") == "ok" else 1

    return _render_human(ctx, report, raw=bool(opts.get("raw")))


def _fmt_value(value: Any, *, metric: str, raw: bool) -> str:
    if raw:
        if value is None:
            return "—"
        if isinstance(value, float):
            return f"{value:.6g}"
        return str(value)
    return human_metric_value(value, metric=metric)


def _fmt_delta(value: Any, *, metric: str, raw: bool) -> str:
    if value is None:
        return "—"
    if raw:
        if isinstance(value, float):
            return f"{value:+.6g}" if value != 0 else "0"
        try:
            n = int(value)
            return f"{n:+d}" if n != 0 else "0"
        except (TypeError, ValueError):
            return str(value)
    return human_delta(value, metric=metric)


def _render_human(ctx: CliContext, report: dict[str, Any], *, raw: bool) -> int:
    from rich.panel import Panel
    from rich.table import Table

    state = report.get("state")
    border = "green" if state == "ok" else "red"
    summary = report.get("summary") or {}
    timing = report.get("timing") or {}
    recipe_meta = report.get("recipe_meta") or {}

    recipe_ms = timing.get("recipe_ms")
    total_ms = timing.get("total_ms")
    if raw:
        recipe_ms_s = f"{recipe_ms}"
        total_ms_s = f"{total_ms}"
    else:
        recipe_ms_s = human_duration_ms(recipe_ms)
        total_ms_s = human_duration_ms(total_ms)

    header = (
        f"[bold]recipe[/] {report.get('recipe')!r}  "
        f"[bold]n[/] {report.get('iterations')}  "
        f"[bold]state[/] {state}\n"
        f"ops={recipe_meta.get('ops')}  "
        f"path={recipe_meta.get('path') or recipe_meta.get('kind') or '—'}  "
        f"recipe={recipe_ms_s}  "
        f"total={total_ms_s}\n"
        f"[dim]source={report.get('source')}  "
        f"kind={report.get('kind')}  "
        f"capability={report.get('capability_id')}[/]"
    )
    notes = report.get("notes") or []
    if notes:
        header += "\n[dim]" + " · ".join(str(n) for n in notes) + "[/]"

    ctx.console.print(
        Panel(header, title="Vitality benchmark", border_style=border)
    )

    # Recipe story panel (peak pending, enqueued, …) — why the run mattered.
    story_keys = (
        "enqueued",
        "processed",
        "submit_ok",
        "drained",
        "ticks",
        "peak_pending",
        "pending_after",
        "fallback",
        "note",
        "target",
        "channel",
        "last_present_count",
    )
    story_lines = []
    for key in story_keys:
        if key not in recipe_meta or recipe_meta[key] is None:
            continue
        val = recipe_meta[key]
        if isinstance(val, (int, float)) and not isinstance(val, bool):
            shown = _fmt_value(val, metric=key, raw=raw)
        else:
            shown = str(val)
        story_lines.append(f"[cyan]{key}[/]: {shown}")
    if story_lines:
        ctx.console.print(
            Panel(
                "\n".join(story_lines),
                title="Recipe story",
                border_style="cyan",
            )
        )

    diff = report.get("diff") or {}
    table = Table(
        title="Load point deltas" + ("" if raw else " (human units)"),
        show_lines=False,
    )
    table.add_column("metric", style="cyan")
    table.add_column("before", justify="right")
    table.add_column("after", justify="right")
    table.add_column("delta", justify="right")

    rows: list[tuple[str, Any, Any, Any]] = []
    for key, cell in sorted(diff.items()):
        if not isinstance(cell, dict):
            continue
        if key in {"sample_ts", "rss_kind"}:
            continue
        rows.append(
            (
                key,
                cell.get("before"),
                cell.get("after"),
                cell.get("delta"),
            )
        )
    rows.sort(
        key=lambda r: (
            0 if r[3] not in (None, 0, 0.0) else 1,
            str(r[0]),
        )
    )
    for key, before, after, delta in rows:
        delta_s = _fmt_delta(delta, metric=key, raw=raw)
        style = ""
        if isinstance(delta, (int, float)) and delta != 0:
            style = "bold yellow"
        table.add_row(
            key,
            _fmt_value(before, metric=key, raw=raw),
            _fmt_value(after, metric=key, raw=raw),
            f"[{style}]{delta_s}[/]" if style else delta_s,
        )
    ctx.console.print(table)

    deltas = summary.get("deltas") or {}
    moved = {k: v for k, v in deltas.items() if v not in (None, 0, 0.0)}
    if moved:
        lines = []
        for k, v in sorted(moved.items()):
            lines.append(f"{k}: {_fmt_delta(v, metric=k, raw=raw)}")
        ctx.console.print(
            Panel(
                "\n".join(lines),
                title="Non-zero deltas",
                border_style="yellow",
            )
        )
    else:
        ctx.console.print(
            "[dim]No non-zero projection deltas "
            "(check Recipe story for enqueue/peak_pending).[/]"
        )

    unit_hint = "raw numbers" if raw else "human units"
    ctx.console.print(
        f"[dim]Tip:[/] [cyan]benchmark work_cycle -n 20[/] · "
        f"[cyan]benchmark log_fill -n 25[/] · "
        f"[cyan]benchmark --json[/] · [cyan]benchmark --raw[/] ({unit_hint}) · "
        "recipes: " + ", ".join(sorted(KNOWN_RECIPES))
    )
    return 0 if state == "ok" else 1


__all__ = ["cmd_benchmark"]
