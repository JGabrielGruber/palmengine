# Tests, coverage & CI — findings (SHA 8413d0e)

## Suite does not pass on master (headline)
Full run: `uv run --with pytest-cov pytest --cov=src/palm` → **exit 1, 19 failures** on a clean
worktree. Every failing file also fails **in isolation** (see `05-isolation-experiment.txt`) → these
are genuine, not ordering/global-state artifacts. Real tracebacks (intended `--extra cli --extra mcp
--group dev` env) show one recurring mechanism: **tests and test doubles lagged production API changes**
from the 0.45.x feature-per-patch cadence, and no CI runs the suite so failures accumulated silently.

Representative root causes (verified):
- `tests/test_mcp_tools.py::test_palm_flows_session_input_tool` — `TypeError: _FakeRestClient.flows_session_input()
  got an unexpected keyword argument 'input_token'` → production `runtimes/mcp/flows/tools.py:194` passes a new
  `input_token=`; the test's `_FakeRestClient` fake signature was never updated.
- `tests/test_design_dispatch.py::test_resolve_design_command_covers_registry` — `KeyError: 'propose_dashboard'`
  → a new design command exists; the test's `_CONCRETE_PATHS` map wasn't updated.
- `tests/test_modular_apps.py::test_palm_provider_app_manifest` — asserts `app.actions == (4 items)` but the palm
  provider now declares 9 (`+list_jobs/list_instances/list_waiting/list_flows/list_resources`). **This is a
  guard-common fitness test — so `just check`/`just guard-common` is RED on master.**
- `test_flows_dispatch` (AttributeError), `test_server_wizards` (response/assert drift), `test_server_studio`,
  `test_rest_api_routes`, `test_server_docs`, `test_palm_provider`, `test_mcp_phase3`,
  `test_conversation_replay_inspect_guard`, `test_design_contributor_hooks`, `test_server_wizard_resume` — same
  family (stale assertions / drifted fakes / renamed attrs).

Full failing list (19): see `grep '^FAILED' 05-pytest-cov.log`.

## Coverage — 80.2% overall (with failures present; passing-path coverage slightly lower)
Per-layer (worst → best): **runtimes 69.6%** (6910/9934, biggest + coldest layer) · app 78.1% · services 79.4% ·
providers 79.4% · storages 84.7% · common 84.8% · patterns 87.2% · **core 92.8%** · definitions 95.6% ·
instances 99.1%. Full data: `05-coverage-by-layer.txt`, `coverage.json`.

Coldest files (all in runtimes, and they coincide with the complexity + churn hotspots):
`mcp/assist/rest_map.py` 6.5% · `cli/tui/prompt.py` 11% · `cli/tui/completion.py` 15% · `mcp/assist/operator.py`
17% · `rest/design/handlers.py` 18% · `rest/assist/handlers.py` 22% · `mcp/rest_client.py` 26% ·
`mcp/in_process.py` **35%** (435 stmts, high-churn, high-complexity). No `--cov-fail-under` gate exists.

## Untested DB adapters (confirmed)
`providers/postgres`, `providers/graphql`, `storages/postgres`, `storages/mongodb` have **only** registry-presence
assertions (`test_modular_apps.py`) + a lazy-registration check (`test_storage.py`) — no behavioral round-trips.
Consistent with `pyproject.toml` empty extras `postgres = []`, `mongodb = []` (drivers unpinned). Provider
docstrings say "(placeholder)". Evidence: `05-adapter-gaps.txt`.

## Test isolation — latent risk (NOT currently causing the failures)
`tests/conftest.py:52` `_isolate_coconut_kv_state` is autouse but **early-returns unless `"coconut"` is in the
nodeid**; only coconut tests reset the two module-level singletons `clear_memory_kv_store()`
(`common/resource/document_storage.py`) and `clear_palm_runtime()`
(`providers/palm/bindings/runtimes/wiring.py`). Other tests that touch this global state must self-reset. The
isolation experiment showed the 19 failures reproduce in isolation, so this fixture is a **design-level
fragility / xdist hazard**, not the cause of today's red suite. Confidence: probable.

## CI / tooling gaps
- Only `.github/workflows/publish.yml` (build+publish). **No workflow runs tests/lint/typecheck/guards** →
  nothing catches the red suite above.
- `.pre-commit-config.yaml` **absent** although `just setup` runs `pre-commit install` and `pre-commit` is a dev
  dep — the hook install has nothing to run.
- No coverage threshold. `pytest-cov` not in the base venv (needs `--group dev`).
- Audit tools (`vulture/radon/xenon/bandit/pip-audit`) referenced by `justfile` recipes but declared **nowhere**
  in pyproject → `just audit`/`complexity`/`refactor` fail on a fresh checkout.
- No Python-version matrix despite advertising 3.11/3.12/3.13.
