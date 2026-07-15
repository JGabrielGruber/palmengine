"""Explorer POST handlers — flow submission and interactive job input."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from palm.common.child_wait import resume_child_wait_for_instance
from palm.common.cqrs.command import ProvideInputCommand, SubmitFlowCommand
from palm.common.exceptions import InstanceNotFoundError
from palm.common.interactive_runtime import resolve_interactive_job
from palm.common.operator.collection_input import resolve_wizard_form_input
from palm.common.runtimes.server.protocol import ServerRequest, ServerResponse
from palm.common.runtimes.server.ssr.render import html_response, redirect
from palm.core.orchestration import JobStatus
from palm.core.orchestration.exceptions import JobNotFoundError
from palm.patterns.wizard.bindings.cqrs.commands import (
    ProvideWizardInputCommand,
    RequestWizardBacktrackCommand,
)
from palm.runtimes.server.surfaces.ssr.explorer.components import (
    assist_handoff_result,
    assist_workspace,
    wizard_workspace,
)
from palm.runtimes.server.surfaces.ssr.explorer.fetch import ExplorerFetcher
from palm.runtimes.server.surfaces.ssr.explorer.forms import coerce_job_input, parse_form_values
from palm.runtimes.server.surfaces.ssr.explorer.pages.utils import is_htmx_request
from palm.runtimes.server.surfaces.ssr.explorer.pages.wizards import _estimate_step_total
from palm.runtimes.server.surfaces.ssr.explorer.schemas import build_flow_submit_schema

if TYPE_CHECKING:
    from palm.runtimes.server.context import ServerContext


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

    def provide_wizard_input(self, request: ServerRequest, *, instance_id: str) -> ServerResponse:
        wizard = self._fetch.get_wizard(instance_id)
        if wizard is None:
            return redirect(f"/explorer/instances/{instance_id}?error=Wizard+not+found")

        form_data = request.body or {}
        prompt = wizard.get("prompt") or {}
        pattern = {
            "field_type": prompt.get("field_type"),
            "effective_schema_type": prompt.get("effective_schema_type"),
            "choices": prompt.get("choices"),
        }

        try:
            resolved = resolve_wizard_form_input(form_data, wizard)
            if isinstance(resolved, tuple):
                self._execute_collection_compound(instance_id, resolved)
            else:
                value = coerce_job_input(str(resolved), pattern)
                self._ctx.execute(ProvideWizardInputCommand(instance_id=instance_id, value=value))
        except InstanceNotFoundError:
            return self._wizard_action_response(
                request,
                instance_id,
                error="Wizard not found",
            )
        except (TypeError, ValueError, RuntimeError) as exc:
            return self._wizard_action_response(
                request,
                instance_id,
                error=str(exc),
            )

        self._ctx.wait_until_idle()
        return self._wizard_action_response(request, instance_id, notice="Input accepted")

    def _execute_collection_compound(
        self,
        instance_id: str,
        resolved: tuple[str, ...],
    ) -> None:
        kind = resolved[0]
        index = int(resolved[1])
        selection = str(index + 1)
        if kind == "__compound_edit__":
            self._ctx.execute(
                ProvideWizardInputCommand(instance_id=instance_id, value="Edit an item")
            )
            self._ctx.wait_until_idle()
            self._ctx.execute(ProvideWizardInputCommand(instance_id=instance_id, value=selection))
            return
        if kind == "__compound_remove__":
            self._ctx.execute(
                ProvideWizardInputCommand(instance_id=instance_id, value="Remove an item")
            )
            self._ctx.wait_until_idle()
            self._ctx.execute(ProvideWizardInputCommand(instance_id=instance_id, value=selection))
            return
        raise ValueError(f"Unsupported collection compound action: {kind}")

    def resume_child_wait(self, request: ServerRequest, *, instance_id: str) -> ServerResponse:
        try:
            resume_child_wait_for_instance(self._ctx.runtime, instance_id)
        except (InstanceNotFoundError, RuntimeError) as exc:
            return self._wizard_action_response(
                request,
                instance_id,
                error=str(exc),
            )

        self._ctx.wait_until_idle()
        return self._wizard_action_response(
            request,
            instance_id,
            notice="Checked nested wizard status",
        )

    def resume_wizard_tick(self, request: ServerRequest, *, instance_id: str) -> ServerResponse:
        """Re-drive a waiting wizard (e.g. auto-run a resource step)."""
        try:
            job = resolve_interactive_job(self._ctx.runtime, instance_id)
            if job.status != JobStatus.WAITING_FOR_INPUT:
                raise RuntimeError(
                    f"Instance {instance_id!r} is not waiting for input "
                    f"(status={job.status.value})"
                )
            self._ctx.runtime.orchestration.resume_job(job.id)
        except (InstanceNotFoundError, RuntimeError) as exc:
            return self._wizard_action_response(
                request,
                instance_id,
                error=str(exc),
            )

        self._ctx.wait_until_idle()
        return self._wizard_action_response(
            request,
            instance_id,
            notice="Wizard advanced",
        )

    def backtrack_wizard(self, request: ServerRequest, *, instance_id: str) -> ServerResponse:
        form_data = request.body or {}
        to_step = _optional_str(form_data.get("to_step"))

        try:
            self._ctx.execute(
                RequestWizardBacktrackCommand(instance_id=instance_id, to_step=to_step)
            )
        except InstanceNotFoundError:
            return self._wizard_action_response(
                request,
                instance_id,
                error="Wizard not found",
            )
        except (TypeError, ValueError) as exc:
            return self._wizard_action_response(
                request,
                instance_id,
                error=str(exc),
            )

        self._ctx.wait_until_idle()
        label = to_step or "previous step"
        return self._wizard_action_response(
            request,
            instance_id,
            notice=f"Backtracked to {label}",
        )

    def _wizard_action_response(
        self,
        request: ServerRequest,
        instance_id: str,
        *,
        notice: str = "",
        error: str = "",
    ) -> ServerResponse:
        if is_htmx_request(request):
            wizard = self._fetch.get_wizard(instance_id)
            instance = self._fetch.get_instance(instance_id) or {}
            if wizard is None:
                return html_response(
                    '<div id="wizard-workspace" class="wizard-workspace">'
                    '<p class="alert alert-error">Wizard not found.</p></div>',
                    status=404,
                )
            body = wizard_workspace(
                instance_id,
                wizard,
                notice=notice,
                error=error,
                total_steps=_estimate_step_total(self._fetch, wizard, instance),
            )
            return html_response(body)

        if error:
            return redirect(f"/explorer/instances/{instance_id}?error={_quote(error)}")
        return redirect(f"/explorer/instances/{instance_id}?notice={_quote(notice)}")

    def provide_assist_input(self, request: ServerRequest, *, session_id: str) -> ServerResponse:
        form_data = request.body or {}
        raw_value = str(form_data.get("value", "")).strip()
        if not raw_value:
            return self._assist_action_response(
                request,
                session_id,
                error="Value is required",
            )
        try:
            self._fetch.provide_assist_input(session_id, raw_value)
        except Exception as exc:
            return self._assist_action_response(request, session_id, error=str(exc))

        self._ctx.wait_until_idle()
        return self._assist_action_response(request, session_id, notice="Answer accepted")

    def backtrack_assist(self, request: ServerRequest, *, session_id: str) -> ServerResponse:
        form_data = request.body or {}
        to_step = _optional_str(form_data.get("to_step"))
        try:
            self._fetch.backtrack_assist_session(session_id, to_step)
        except Exception as exc:
            return self._assist_action_response(request, session_id, error=str(exc))

        self._ctx.wait_until_idle()
        label = to_step or "previous step"
        return self._assist_action_response(request, session_id, notice=f"Backtracked to {label}")

    def cancel_assist(self, request: ServerRequest, *, session_id: str) -> ServerResponse:
        try:
            self._fetch.cancel_assist_session(session_id)
        except Exception as exc:
            return redirect(f"/explorer/assist/session/{session_id}?error={_quote(str(exc))}")

        self._ctx.wait_until_idle()
        return redirect("/explorer/assist?notice=Assist+session+cancelled")

    def handoff_assist(self, request: ServerRequest, *, session_id: str) -> ServerResponse:
        try:
            result = self._fetch.handoff_assist_session(session_id)
        except Exception as exc:
            return self._assist_action_response(request, session_id, error=str(exc))

        self._ctx.wait_until_idle()
        if is_htmx_request(request):
            return html_response(assist_handoff_result(session_id, result))

        handoff = result.get("handoff") if isinstance(result.get("handoff"), dict) else {}
        if handoff.get("kind") == "flow" and handoff.get("flow_id"):
            from urllib.parse import quote

            flow_id = str(handoff["flow_id"])
            return redirect(
                f"/explorer/flows/submit?flow={quote(flow_id, safe='')}&notice=Handoff+ready"
            )
        return redirect(f"/explorer/assist/session/{session_id}?notice=Handoff+complete")

    def _assist_action_response(
        self,
        request: ServerRequest,
        session_id: str,
        *,
        notice: str = "",
        error: str = "",
    ) -> ServerResponse:
        if is_htmx_request(request):
            try:
                view = self._fetch.get_assist_session(session_id)
            except Exception:
                return html_response(
                    '<div id="assist-workspace" class="assist-workspace">'
                    '<p class="alert alert-error">Assist session not found.</p></div>',
                    status=404,
                )
            return html_response(
                assist_workspace(session_id, view, notice=notice, error=error)
            )

        if error:
            return redirect(f"/explorer/assist/session/{session_id}?error={_quote(error)}")
        return redirect(f"/explorer/assist/session/{session_id}?notice={_quote(notice)}")

    def start_assist_scenario(
        self,
        request: ServerRequest,
        *,
        scenario_id: str,
    ) -> ServerResponse:
        try:
            view = self._fetch.start_assist_scenario(scenario_id)
        except Exception as exc:
            return redirect(
                f"/explorer/assist/scenarios/{_quote(scenario_id)}?error={_quote(str(exc))}"
            )

        self._ctx.wait_until_idle()
        session_id = view.get("session_id")
        if not session_id:
            return redirect(f"/explorer/assist?error={_quote('Assist start returned no session_id')}")
        return redirect(f"/explorer/assist/session/{session_id}")

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
