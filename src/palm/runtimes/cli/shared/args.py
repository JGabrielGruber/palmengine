"""
CLI argument definitions and PalmSettings merge helpers.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from palm import __version__
from palm.app.cli_settings import resolve_cli_settings
from palm.app.settings import PalmSettings, SchedulerPolicy

_CLI_EPILOG = """
examples:
  palm                          interactive REPL (default)
  palm status                 live projection dashboard (default)
  palm status --brief         compact engine summary
  palm doctor                 full engine health report
  palm doctor --dashboard     same as palm status
  palm flow start onboard
  palm start parallel-demo
  palm --storage-backend filesystem wizard start onboard
  palm instance list --all --format json

settings precedence (highest last):
  PALM_* environment variables → --config file → CLI flags

documentation:
  README.md · DEVELOPMENT.md · ARCHITECTURE.md
"""


@dataclass
class CliInvocation:
    """Parsed CLI invocation — bootstrap options and command routing."""

    command: str | None
    storage_backend: str | None = None
    data_dir: Path | None = None
    config: Path | None = None
    enable_state_snapshot: bool | None = None
    max_loaded_instances: int | None = None
    max_concurrent_active: int | None = None
    default_scheduler: SchedulerPolicy | None = None
    output_format: str = "table"
    process_cmd: str | None = None
    instance_cmd: str | None = None
    wizard_cmd: str | None = None
    flow_cmd: str | None = None
    ref: str | None = None
    instance_id: str | None = None
    flow: str | None = None
    full: bool = False
    dashboard: bool = False
    brief: bool = False
    input_args: list[str] | None = None
    instance_list_all: bool = False
    instance_status: str | None = None
    instance_flow: str | None = None
    instance_limit: int | None = None
    prune_dry_run: bool = False
    host_cmd: str | None = None
    host_workers: int | None = None
    host_bind: str | None = None
    host_port: int | None = None


def add_global_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--version", action="version", version=f"Palm {__version__}")
    parser.add_argument(
        "-b",
        "--storage-backend",
        default=None,
        help="Storage backend (env: PALM_STORAGE_BACKEND, default: memory)",
    )
    parser.add_argument(
        "-d",
        "--data-dir",
        type=Path,
        default=None,
        help="Data directory (env: PALM_DATA_DIR)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help="Optional .env-style config file (overrides default .env)",
    )
    parser.add_argument(
        "-S",
        "--enable-state-snapshot",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Capture state snapshots (env: PALM_ENABLE_STATE_SNAPSHOT)",
    )
    parser.add_argument(
        "--max-loaded-instances",
        type=int,
        default=None,
        help="InstanceManager LRU size (env: PALM_MAX_LOADED_INSTANCES)",
    )
    parser.add_argument(
        "--max-concurrent-active",
        type=int,
        default=None,
        help="Active instance cap (env: PALM_MAX_CONCURRENT_ACTIVE)",
    )
    parser.add_argument(
        "--scheduler",
        choices=("inline", "queued"),
        default=None,
        help="Default scheduler policy (env: PALM_DEFAULT_SCHEDULER)",
    )
    parser.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format for list/status tables (default: table)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="palm",
        description=f"Palm Engine — workflow orchestration ({__version__})",
        epilog=_CLI_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_global_arguments(parser)

    sub = parser.add_subparsers(dest="command", metavar="command")
    sub.add_parser("repl", help="Interactive REPL (default)")

    version_p = sub.add_parser("version", help="Show version information")
    version_p.add_argument("--full", action="store_true")

    status_p = sub.add_parser("status", help="Live dashboard or instance status")
    status_p.add_argument(
        "--dashboard",
        action="store_true",
        help="Show projection dashboard (default when no instance id)",
    )
    status_p.add_argument("--brief", action="store_true", help="Compact engine summary")
    status_p.add_argument("--full", action="store_true", help="Full doctor report")
    status_p.add_argument("instance_id", nargs="?", default=None)

    doctor_p = sub.add_parser("doctor", help="Engine health, persistence, and instances")
    doctor_p.add_argument(
        "--dashboard",
        action="store_true",
        help="Show projection dashboard instead of full doctor report",
    )

    proc = sub.add_parser("process", help="Process definition commands")
    proc_sub = proc.add_subparsers(dest="process_cmd", required=True)
    proc_sub.add_parser("list")
    submit_p = proc_sub.add_parser("submit")
    submit_p.add_argument("ref")
    resume_p = proc_sub.add_parser(
        "resume",
        help="Resume instance (alias: palm instance resume)",
    )
    resume_p.add_argument("instance_id")

    inst = sub.add_parser("instance", help="Process instance commands")
    inst_sub = inst.add_subparsers(dest="instance_cmd", required=True)
    list_p = inst_sub.add_parser("list", help="List instances (active by default)")
    list_p.add_argument("--all", action="store_true", help="Include terminal instances")
    list_p.add_argument("--status", help="Filter by status")
    list_p.add_argument("--flow", help="Filter by flow name")
    list_p.add_argument("--limit", type=int, help="Max rows")
    inst_status = inst_sub.add_parser(
        "status",
        help="Instance detail, or dashboard when no id (alias: palm status)",
    )
    inst_status.add_argument("instance_id", nargs="?", default=None)
    snapshots_p = inst_sub.add_parser("snapshots")
    snapshots_p.add_argument("instance_id")
    resume_inst = inst_sub.add_parser("resume")
    resume_inst.add_argument("instance_id")
    prune_p = inst_sub.add_parser("prune", help="Remove terminal instances from storage")
    prune_p.add_argument("--dry-run", action="store_true")

    flow = sub.add_parser("flow", help="Flow commands (any pattern)")
    flow_sub = flow.add_subparsers(dest="flow_cmd", required=True)
    flow_sub.add_parser("list", help="List all registered flows")
    flow_start_p = flow_sub.add_parser("start", help="Start a flow by name or id")
    flow_start_p.add_argument("flow")

    start_p = sub.add_parser("start", help="Start any flow by name (shortcut)")
    start_p.add_argument("flow")

    wiz = sub.add_parser("wizard", help="Wizard flow commands (shortcut)")
    wiz_sub = wiz.add_subparsers(dest="wizard_cmd", required=True)
    wiz_sub.add_parser("list")
    wiz_start_p = wiz_sub.add_parser("start")
    wiz_start_p.add_argument("flow")

    for name in ("input", "back"):
        p = sub.add_parser(name)
        p.add_argument("args", nargs=argparse.REMAINDER)

    host = sub.add_parser("host", help="Run ApplicationHost deployment roles")
    host_sub = host.add_subparsers(dest="host_cmd", required=True)
    host_sub.add_parser(
        "all-in-one",
        aliases=["all_in_one"],
        help="Collapsed master+worker process (default host profile)",
    )
    host_sub.add_parser("master", help="Command acceptance and outbox processor")
    worker_p = host_sub.add_parser("worker", help="Background job-driving workers")
    worker_p.add_argument(
        "--workers",
        type=int,
        default=None,
        help="Number of daemon worker runtimes (default: 1)",
    )
    server_p = host_sub.add_parser("server", help="HTTP API with queued job driving")
    server_p.add_argument("--host", default=None, help="Bind host (default: 127.0.0.1)")
    server_p.add_argument("--port", type=int, default=None, help="Bind port (default: 8080)")

    return parser


def settings_from_invocation(inv: CliInvocation) -> PalmSettings:
    """Merge env, optional config file, and explicit CLI flags into PalmSettings."""
    base = PalmSettings.from_env_file(inv.config) if inv.config is not None else PalmSettings()

    return resolve_cli_settings(
        storage_backend=inv.storage_backend,
        data_dir=inv.data_dir,
        settings=base,
        enable_state_snapshot=inv.enable_state_snapshot,
        max_loaded_instances=inv.max_loaded_instances,
        max_concurrent_active=inv.max_concurrent_active,
        default_scheduler=inv.default_scheduler,
    )


def invocation_from_namespace(args: argparse.Namespace) -> CliInvocation:
    return CliInvocation(
        command=args.command,
        storage_backend=args.storage_backend,
        data_dir=args.data_dir,
        config=args.config,
        enable_state_snapshot=args.enable_state_snapshot,
        max_loaded_instances=args.max_loaded_instances,
        max_concurrent_active=args.max_concurrent_active,
        default_scheduler=args.scheduler,
        output_format=args.format,
        process_cmd=getattr(args, "process_cmd", None),
        instance_cmd=getattr(args, "instance_cmd", None),
        wizard_cmd=getattr(args, "wizard_cmd", None),
        flow_cmd=getattr(args, "flow_cmd", None),
        ref=getattr(args, "ref", None),
        instance_id=getattr(args, "instance_id", None),
        flow=getattr(args, "flow", None),
        full=getattr(args, "full", False),
        dashboard=getattr(args, "dashboard", False),
        brief=getattr(args, "brief", False),
        input_args=getattr(args, "args", None),
        instance_list_all=getattr(args, "all", False),
        instance_status=getattr(args, "status", None),
        instance_flow=getattr(args, "flow", None),
        instance_limit=getattr(args, "limit", None),
        prune_dry_run=getattr(args, "dry_run", False),
        host_cmd=getattr(args, "host_cmd", None),
        host_workers=getattr(args, "workers", None),
        host_bind=getattr(args, "host", None),
        host_port=getattr(args, "port", None),
    )
