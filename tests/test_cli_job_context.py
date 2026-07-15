"""Tests for CLI job context extraction — wizard and parallel flows."""

from __future__ import annotations

import json
from io import StringIO

from rich.console import Console

from palm.common.job_inspection import (
    format_step_context,
    inspect_job,
    inspect_job_json,
)
from palm.common.patterns import PatternBuildContext, build_pattern
from palm.core.behavior_tree import PatternStatus
from palm.core.event import EventEngine
from palm.definitions import FlowDefinition
from palm.patterns.parallel.pattern import ParallelPattern
from palm.runtimes.cli.commands.registry import build_registry
from palm.states import BlackboardState


def _parallel_flow() -> FlowDefinition:
    return FlowDefinition(
        name="parallel-cli-test",
        pattern="parallel",
        state_schema={
            "type": "object",
            "properties": {
                "alpha": {"type": "object"},
                "beta": {"type": "object"},
            },
            "required": ["alpha", "beta"],
        },
        options={
            "merge_strategy": "all",
            "branches": [
                {
                    "slug": "alpha",
                    "pattern": "wizard",
                    "options": {
                        "steps": [
                            {
                                "slug": "name",
                                "title": "Name",
                                "prompt": "Alpha name?",
                            },
                        ],
                    },
                    "result_key": "alpha",
                },
                {
                    "slug": "beta",
                    "pattern": "wizard",
                    "options": {
                        "steps": [
                            {
                                "slug": "team",
                                "title": "Team",
                                "prompt": "Beta team?",
                            },
                        ],
                    },
                    "result_key": "beta",
                },
            ],
        },
    )


def _wizard_flow() -> FlowDefinition:
    return FlowDefinition(
        name="wizard-cli-test",
        pattern="wizard",
        state_schema={"type": "object", "properties": {"name": {"type": "string"}}},
        options={
            "steps": [
                {
                    "slug": "name",
                    "title": "Name",
                    "prompt": "Your name?",
                    "state_schema": {"type": "string", "minLength": 1},
                },
            ],
        },
    )


def _job_from_flow(flow: FlowDefinition):
    from palm.core.orchestration import Job, JobStatus

    built = build_pattern(flow, context=PatternBuildContext())
    schema = flow.materialize_state_schema()
    state = BlackboardState(schema=schema)
    pattern_status = built.tick(state)
    if pattern_status == PatternStatus.WAITING_FOR_INPUT:
        job_status = JobStatus.WAITING_FOR_INPUT
    elif pattern_status == PatternStatus.SUCCESS:
        job_status = JobStatus.SUCCEEDED
    else:
        job_status = JobStatus.RUNNING
    return Job(id="job-test", executable=built, state=state, status=job_status)


def test_inspect_wizard_job_includes_scope_and_schema() -> None:
    job = _job_from_flow(_wizard_flow())
    ctx = inspect_job(job)

    assert ctx.pattern == "wizard"
    assert ctx.step == "name"
    assert ctx.scope_path == "name"
    assert ctx.effective_schema_type == "string"
    assert ctx.prompt == "Your name?"


def test_inspect_parallel_job_includes_branches() -> None:
    job = _job_from_flow(_parallel_flow())
    ctx = inspect_job(job)

    assert ctx.pattern == "parallel"
    assert len(ctx.branches) == 2
    assert {branch.slug for branch in ctx.branches} == {"alpha", "beta"}
    assert ctx.active_branch in {"alpha", "beta"}
    assert ctx.branch_progress == "0/2"
    assert ctx.repl_scope_suffix.startswith("@parallel:")
    assert ctx.prompt in {"Alpha name?", "Beta team?"}


def test_inspect_job_json_serializable() -> None:
    job = _job_from_flow(_parallel_flow())
    payload = inspect_job_json(job)

    assert payload["pattern"] == "parallel"
    assert "branches" in payload
    assert payload["branch_progress"] == "0/2"
    json.dumps(payload)


def test_format_step_context_parallel_slug() -> None:
    assert format_step_context("alpha:name") == "parallel:alpha > name"
    assert format_step_context("beta") == "beta"
    assert format_step_context(None) == "—"


def test_status_json_uses_job_context(cli_ctx) -> None:
    reg = build_registry()
    reg.dispatch(cli_ctx, "flow start parallel-demo")
    iid = cli_ctx.active_instance_id
    assert iid is not None

    cli_ctx.output_format = "json"
    buf = StringIO()
    cli_ctx.console = Console(file=buf, force_terminal=False, width=120)
    assert reg.dispatch(cli_ctx, f"status {iid}") == 0

    payload = json.loads(buf.getvalue())
    assert payload["pattern"] == "parallel"
    assert "branches" in payload
    assert payload["branch_progress"] == "0/2"


def test_parallel_branch_waiting_event() -> None:
    events: list[str] = []
    engine = EventEngine()
    engine.initialize()
    engine.subscribe("*", lambda event: events.append(event.type))

    flow = _parallel_flow()
    built = build_pattern(
        flow,
        context=PatternBuildContext(event_engine=engine),
    )
    assert isinstance(built, ParallelPattern)
    state = BlackboardState(schema=flow.materialize_state_schema())
    built.tick(state)

    assert "parallel.branch_waiting" in events
