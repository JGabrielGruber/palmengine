"""0.61.11 — Inspect presents benchmark tool; CLI thin present."""

from __future__ import annotations

from bundles.standard.app.host.application_host import ApplicationHost
from bundles.standard.app.host.roles import DeploymentProfile
from bundles.standard.app.settings import PalmSettings
from bundles.standard.runtimes.cli.commands.benchmark import cmd_benchmark
from bundles.standard.runtimes.cli.commands.registry import build_registry
from bundles.standard.runtimes.cli.shared.args import (
    build_parser,
    invocation_from_namespace,
)
from bundles.standard.runtimes.cli.shared.context import CliContext
from bundles.standard.runtimes.cli.shared.dispatch import dispatch_invocation
from palm.services.inspect import present_benchmark
from palm.system.log import reset_system_log_for_tests
from palm.system.vitality import RECIPE_LOG_FILL, RECIPE_PULSE


class _QuietConsole:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def print(self, *args: object, **kwargs: object) -> None:
        self.messages.append(" ".join(str(a) for a in args))

    def print_json(self, *, data: object = None, **kwargs: object) -> None:
        self.messages.append(f"json:{data!r}"[:200])


def _started_host() -> ApplicationHost:
    reset_system_log_for_tests()
    host = ApplicationHost(
        settings=PalmSettings.for_tests(load_examples=False),
        profile=DeploymentProfile.all_in_one(),
        boot_mode="test",
    )
    host.start()
    return host


def test_inspect_benchmark_envelope() -> None:
    host = _started_host()
    try:
        rt = host.runtime()
        assert host.inspect is not None
        report = host.inspect.benchmark(rt, recipe=RECIPE_PULSE, iterations=3)
        assert report["source"] == "palm.system.vitality"
        assert report["kind"] == "benchmark_present"
        assert report["role"] == "tool_present"
        assert report["capability_id"] == "benchmark"
        assert report["state"] == "ok"
        assert report["recipe"] == RECIPE_PULSE
        assert report["iterations"] == 3
        assert "diff" in report and "summary" in report
        assert "deltas" in report["summary"]
        # Present does not invent metrics — fragment path only.
        assert report["before"].get("seat_present") is not None
    finally:
        host.shutdown()


def test_present_benchmark_matches_service() -> None:
    host = _started_host()
    try:
        rt = host.runtime()
        a = present_benchmark(rt, recipe=RECIPE_LOG_FILL, iterations=5)
        b = host.inspect.benchmark(rt, recipe=RECIPE_LOG_FILL, iterations=5)
        assert a["kind"] == b["kind"] == "benchmark_present"
        assert a["recipe"] == b["recipe"] == RECIPE_LOG_FILL
    finally:
        host.shutdown()


def test_cli_cmd_benchmark_json() -> None:
    host = _started_host()
    try:
        console = _QuietConsole()
        ctx = CliContext(host=host, console=console, output_format="json")
        code = cmd_benchmark(ctx, ["--recipe", "idle", "-n", "2", "--json"])
        assert code == 0
        assert any("json:" in m or "benchmark" in m.lower() for m in console.messages) or console.messages
        # JSON path should have emitted something.
        assert console.messages
    finally:
        host.shutdown()


def test_cli_registry_and_dispatch_line() -> None:
    host = _started_host()
    try:
        console = _QuietConsole()
        ctx = CliContext(host=host, console=console)
        reg = build_registry()
        code = reg.dispatch(ctx, "benchmark pulse -n 2")
        assert code == 0
        blob = "\n".join(console.messages)
        assert "pulse" in blob.lower() or "Vitality" in blob or "recipe" in blob.lower()
    finally:
        host.shutdown()


def test_argparse_benchmark_invocation() -> None:
    parser = build_parser()
    # Global --format must precede the subcommand.
    ns = parser.parse_args(["--format", "json", "benchmark", "log_fill", "-n", "7"])
    inv = invocation_from_namespace(ns)
    assert inv.command == "benchmark"
    assert inv.benchmark_recipe == "log_fill"
    assert inv.benchmark_iterations == 7
    assert inv.output_format == "json"

    host = _started_host()
    try:
        console = _QuietConsole()
        ctx = CliContext(host=host, console=console, output_format=inv.output_format)
        reg = build_registry()
        code = dispatch_invocation(ctx, reg, inv)
        assert code == 0
    finally:
        host.shutdown()
