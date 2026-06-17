# Release checklist — 0.12.0

Compositional Power release: `ResourceDefinition`, `ResourceLeaf`, `palm` provider, compensation, Explorer resources hub.

## Pre-release verification

- [ ] Version bumped: `pyproject.toml` and `src/palm/__init__.py` → **0.12.0**
- [ ] `CHANGELOG.md` — `[0.12.0]` section complete; `[Unreleased]` empty
- [ ] Docs updated: `README.md`, `ARCHITECTURE.md`, `STATUS.md`, `SCOPE.md`, `MIGRATION-0.12.md`, `docs/VISION-0.12.md`, `docs/llms.txt`, `docs/index.html`
- [ ] `MIGRATION-0.12.md` covers wizard `step_kind: resource` breaking change

## Quality gates

```bash
just docs-check       # version surfaces consistent
just check            # lint + mypy + tests + guard-core (~10s)
just full-check       # + demo-full + coverage
just demo-full        # ApplicationHost E2E script
```

Expected: **~612 tests** pass (`pytest --fast` skips slow integration).

Manual smoke:

```bash
palm version --full
palm doctor
palm resource list
palm resource describe fetch-customer   # if example loaded
palm status
palm flow start onboard
palm host server                        # open http://localhost:8080/explorer/resources
```

## Build & publish

```bash
just build                     # wheel + sdist in dist/
ls -lh dist/                   # palmengine-0.12.0-*
```

### TestPyPI (recommended first)

```bash
export TEST_PYPI_TOKEN=pypi-...   # TestPyPI API token
just publish-test
pip install -i https://test.pypi.org/simple/ 'palmengine[cli]==0.12.0'
palm version
palm resource list
```

### Production PyPI

```bash
export PYPI_TOKEN=pypi-...
just publish                   # 5s abort window
```

## Git tag & GitHub

```bash
git add -A
git commit -m "Release 0.12.0 — Compositional Power"
git tag -a v0.12.0 -m "Palm Engine 0.12.0 — Compositional Power"
git push origin master --tags
```

Create GitHub release from tag `v0.12.0`:
- Title: **Palm Engine 0.12.0 — Compositional Power**
- Body: copy `CHANGELOG.md` `[0.12.0]` section
- Attach `dist/*` artifacts if not using CI publish

## Post-release

- [ ] Verify `pip install palmengine[cli]` on clean venv
- [ ] Update website deployment if separate from repo
- [ ] Open `[Unreleased]` in `CHANGELOG.md` for next work

## Breaking-change reminders (communicate in release notes)

| 0.11.x habit | 0.12.0 |
|--------------|--------|
| Wizard `step_kind: action` + `resource_provider` | `step_kind: resource` + `resource_ref` |
| `WizardActionLeaf` | `WizardResourceLeaf` / `ResourceLeaf` |
| `wizard.resource.invoked` event | `resource.*` events from `ResourceEngine` |

Full guide: [MIGRATION-0.12.md](MIGRATION-0.12.md)