"""Explorer POST handlers — flow submission and interactive job input."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import ProvideInputCommand, SubmitFlowCommand
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.fetch import ExplorerFetcher
from palm.common.runtimes.server.ssr.forms import coerce_job_input, parse_form_values
from palm.common.runtimes.server.ssr.render import redirect
from palm.common.runtimes.server.ssr.schemas import FLOW_SUBMIT_FORM
from palm.core.orchestration.exceptions import JobNotFoundError

if TYPE_CHECKING:
    from palm.common.runtimes.server.context import ServerContext


class ExplorerActions:
    """Write-side Explorer routes backed by CQRS commands."""

    def __init__(self, ctx: ServerContext) -> None:
        self._ctx = ctx
        self._fetch = ExplorerFetcher(ctx)

    def provide_job_input(self, request: ServerRequest, *, job_id: str) -> ServerResponse:
        context = self._fetch.get_job_context(job_id)
        if not context.get("found", True):
            return redirect(f"/explorer/jobs/{job_id}?error=Job+not+found")

        form_data = request.body or {}
        raw_value = str(form_data.get("value", ""))
        pattern = context.get("pattern") or {}

        try:
            value = coerce_job_input(raw_value, pattern)
            self._ctx.execute(ProvideInputCommand(job_id=job_id, value=value))
        except JobNotFoundError:
            return redirect(f"/explorer/jobs/{job_id}?error=Job+not+found")
        except (TypeError, ValueError, RuntimeError) as exc:
            return redirect(f"/explorer/jobs/{job_id}?error={_quote(str(exc))}")

        self._ctx.wait_until_idle()
        return redirect(f"/explorer/jobs/{job_id}?notice=Input+accepted")

    def submit_flow(self, request: ServerRequest) -> ServerResponse:
        form_data = request.body or {}
        values, errors = parse_form_values(FLOW_SUBMIT_FORM, form_data)
        if errors:
            joined = _quote("; ".join(errors))
            return redirect(f"/explorer/flows/submit?error={joined}")

        try:
            command = _flow_command_from_form(values)
            job = self._ctx.execute(command)
        except (TypeError, ValueError, KeyError) as exc:
            return redirect(f"/explorer/flows/submit?error={_quote(str(exc))}")
        except Exception as exc:
            return redirect(f"/explorer/flows/submit?error={_quote(str(exc))}")

        self._ctx.wait_until_idle()
        job_id = getattr(job, "id", None) or str(job)
        return redirect(f"/explorer/jobs/{job_id}?notice=Flow+submitted")


def _flow_command_from_form(values: dict[str, Any]) -> SubmitFlowCommand:
    flow_name = str(values.get("flow_name") or "").strip()
    wizard_name = str(values.get("wizard_name") or "").strip()
    wizard_steps = values.get("wizard_steps")

    if wizard_name:
        steps = int(wizard_steps) if wizard_steps else 2
        return SubmitFlowCommand(flow={"wizard": {"name": wizard_name, "steps": steps}})
    if flow_name:
        return SubmitFlowCommand(flow=flow_name)
    raise ValueError("Provide a flow name or wizard name")


def _quote(message: str) -> str:
    from urllib.parse import quote

    return quote(message, safe="")