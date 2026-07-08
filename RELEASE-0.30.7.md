# Release checklist — 0.30.7 (bundled: post-0.26 through Assist design entry)

**Theme:** Local document/KV resources, compositional design parity, and **Assist as the weak-LLM operator surface** for running flows, publishing definitions, and recovering resource failures.

**PyPI version:** **0.30.7**  
**Previous GitHub/PyPI cut:** **0.26.0**  
**Bundles (local micro-releases):** 0.27 · 0.28 · 0.29 · 0.30.0–0.30.6

| Track | Docs |
|-------|------|
| Assist design entry | [VISION-0.30](docs/VISION-0.30.md) · [MIGRATION-0.30](MIGRATION-0.30.md) |
| Compositional design | [VISION-0.27](docs/VISION-0.27.md) · [ADR-010](docs/adr/010-prompt-state-interpolation.md) · [ADR-012](docs/adr/012-wizard-branch-step.md) |
| Local documents / KV | [VISION-0.28](docs/VISION-0.28.md) · [ADR-011](docs/adr/011-local-document-resources.md) |
| Design Service (prior) | [VISION-0.25](docs/VISION-0.25.md) · [MIGRATION-0.25](MIGRATION-0.25.md) |

## What lands (summary)

### Operator / MCP (0.30)

- Design discovery from **operator-entry** (`create-flow`, `improve-flow`, `propose-resource`)
- **`design-entry`** scenario shell; `kind: design` handoff
- **One-shot** `palm_design_publish_flow` / `publish_resource`
- **`palm_assist(params={body})`** → design publish; **`params={flow_id}`** → start flow
- Flows via `palm_assist` default **assistant** format; create re-inspects first turn
- Resource failure CTAs (resume, doctor, publish resource)
- operator-entry: **coconut-npc** demo path

### Compositional + resources (0.27–0.29)

- `coconut-npc` branching reference + **`kv`** persistence
- Prompt `{{ state.* }}` interpolation; `step_kind: branch`
- `kv` / `file` / **tiered** backends; design contributors + doctor preflight
- Resource operator ergonomics (`on_resource_failure`, remediation hints)

## Pre-ship

- [x] Version **0.30.7** in `pyproject.toml` / `palm.__version__` / docs surfaces
- [x] CHANGELOG `[0.30.7]` consolidates Unreleased post-0.26 work
- [x] `MIGRATION-0.30.md` present for assist/design agents
- [ ] `just release-prep` (or targeted pytest below)
- [ ] Tag `v0.30.7`
- [ ] GitHub release notes (see description below)
- [ ] Optional PyPI: `just publish`

## Verify

```bash
uv run pytest \
  tests/test_palm_assist_tool.py \
  tests/test_operator_entry_flow.py \
  tests/test_design_entry_flow.py \
  tests/test_mcp_design_in_process.py \
  tests/test_design_dispatch.py \
  tests/test_kv_provider.py \
  tests/test_file_provider.py \
  tests/test_coconut_npc_flow.py \
  tests/test_coconut_npc_persistence.py \
  tests/test_wizard_branch_step.py \
  -q

just guard-common
```

## Tag

```bash
git tag -a v0.30.7 -m "Palm Engine 0.30.7 — assist operator UX, KV/file resources, compositional design"
```

## Publish (optional)

```bash
just release-prep
# Set PYPI_TOKEN, then:
just publish
```
