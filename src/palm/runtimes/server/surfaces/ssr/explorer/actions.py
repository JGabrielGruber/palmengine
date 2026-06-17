"""Explorer POST handlers — flow submission and interactive job input."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.cqrs.command import ProvideInputCommand, SubmitFlowCommand
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.render import redirect
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.runtimes.server.surfaces.ssr.explorer.fetch import ExplorerFetcher
from palm.runtimes.server.surfaces.ssr.explorer.forms import coerce_job_input, parse_form_values
from palm.runtimes.server.surfaces.ssr.explorer.schemas import build_flow_submit_schema

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
        flows = self._fetch.list_flows()
        schema = build_flow_submit_schema(flows)
        form_data = request.body or {}
        values, errors = parse_form_values(schema, form_data)
        errors.extend(_validate_submit_values(values))

        if errors:
            return redirect(_submit_redirect_url(values, error="; ".join(errors)))

        try:
            command = _flow_command_from_form(values)
            job = self._ctx.execute(command)
        except (TypeError, ValueError, KeyError) as exc:
            return redirect(_submit_redirect_url(values, error=str(exc)))
        except Exception as exc:
            return redirect(_submit_redirect_url(values, error=str(exc)))

        self._ctx.wait_until_idle()
        job_id = getattr(job, "id", None) or str(job)
        return redirect(f"/explorer/jobs/{job_id}?notice=Flow+submitted")


def _validate_submit_values(values: dict[str, Any]) -> list[str]:
    mode = str(values.get("submit_mode") or "registered")
    errors: list[str] = []
    if mode == "inline_wizard":
        if not str(values.get("wizard_name") or "").strip():
            errors.append("wizard_name: required for inline wizard mode")
    else:
        flow_id = str(values.get("flow_id") or values.get("flow_name") or "").strip()
        if not flow_id:
            errors.append("flow_id: choose a registered flow")
    return errors


def _flow_command_from_form(values: dict[str, Any]) -> SubmitFlowCommand:
    mode = str(values.get("submit_mode") or "registered")
    job_id = _optional_str(values.get("job_id"))

    if mode == "inline_wizard":
        wizard_name = str(values.get("wizard_name") or "").strip()
        if not wizard_name:
            raise ValueError("wizard_name is required for inline wizard mode")
        steps = int(values.get("wizard_steps") or 2)
        return SubmitFlowCommand(
            flow={"wizard": {"name": wizard_name, "steps": steps}},
            job_id=job_id,
        )

    flow_id = str(values.get("flow_id") or values.get("flow_name") or "").strip()
    if flow_id:
        return SubmitFlowCommand(flow=flow_id, by_id=True, job_id=job_id)
    raise ValueError("Choose a registered flow or switch to inline wizard mode")


def _submit_redirect_url(values: dict[str, Any], *, error: str) -> str:
    from urllib.parse import quote

    flow_id = str(values.get("flow_id") or "").strip()
    base = f"/explorer/flows/submit?error={quote(error, safe='')}"
    if flow_id:
        base += f"&flow={quote(flow_id, safe='')}"
    return base


def _optional_str(value: object | None) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _quote(message: str) -> str:
    from urllib.parse import quote

    return quote(message, safe="")
