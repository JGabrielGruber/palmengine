"""
REPL prompt styling — context-rich prompt with compact scope/branch suffixes.
"""

from __future__ import annotations

from palm.runtimes.cli.shared.context import CliContext
from palm.runtimes.cli.shared.job_inspect import inspect_job


def build_repl_prompt(ctx: CliContext) -> str:
    """Build the interactive prompt with flow, step, scope, and validation hints."""
    if not ctx.active_instance_id:
        return "palm> "

    short = ctx.active_instance_id[:8]
    suffix = ""

    try:
        job = ctx.job_for_instance(ctx.active_instance_id)
        context = inspect_job(job)

        flow = None
        for summary in ctx.list_instance_summaries():
            if summary.instance_id == ctx.active_instance_id:
                flow = summary.flow_name or summary.process_name
                break

        if flow and context.step:
            suffix = f" {flow}:{context.step}"
        elif flow:
            suffix = f" {flow}"

        scope_suffix = context.repl_scope_suffix
        if scope_suffix and scope_suffix not in suffix:
            suffix = f"{suffix}{scope_suffix}"

        if context.branch_progress and context.pattern == "parallel":
            suffix = f"{suffix} [{context.branch_progress}]"

        if context.validation_error:
            preview = (
                context.validation_error
                if len(context.validation_error) <= 20
                else f"{context.validation_error[:17]}…"
            )
            suffix = f"{suffix} !{preview}"
    except Exception:
        pass

    return f"palm:{short}{suffix} ●> "
