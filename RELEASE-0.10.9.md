# Release checklist — 0.10.9

Architecture evolution release: ApplicationHost, CQRS, reliability primitives, status dashboard, CLI consolidation.

## Pre-release verification

- [ ] Version bumped: `pyproject.toml` and `src/palm/__init__.py` → **0.10.9**
- [ ] `CHANGELOG.md` — `[0.10.9]` section complete; upgrade notes accurate
- [ ] Docs updated: `README.md`, `ARCHITECTURE.md`, `DEVELOPMENT.md`, `examples/README.md`
- [ ] `MIGRATION-0.10.md` reflects current CLI (`status` / `doctor` semantics)

## Quality gates

```bash
just check          # lint + mypy + tests + guard-core (~10s)
just full-check     # + demo-full + coverage
just demo-full      # ApplicationHost E2E script
```

Expected: **~488 tests** pass in **~8s** (`pytest --fast` skips slow integration).

Manual smoke:

```bash
palm status                    # dashboard default
palm status --full             # detailed dashboard
palm status -r                 # live refresh (Ctrl+C)
palm doctor                    # full health report
palm flow start onboard        # host command bus
palm host all-in-one           # blocking host (Ctrl+C)
```

## Build & publish

```bash
just build                     # wheel + sdist in dist/
ls -lh dist/                   # palmengine-0.10.9-*
```

### TestPyPI (recommended first)

```bash
export TEST_PYPI_TOKEN=pypi-...   # TestPyPI API token
just publish-test
pip install -i https://test.pypi.org/simple/ 'palmengine[cli]==0.10.9'
palm version
palm status
```

### Production PyPI

```bash
export PYPI_TOKEN=pypi-...
just publish                   # 5s abort window
```

## Git tag & GitHub

```bash
git add -A
git commit -m "Release 0.10.9 — ApplicationHost, CQRS, dashboard"
git tag -a v0.10.9 -m "Palm Engine 0.10.9 — architecture evolution release"
git push origin master --tags
```

Create GitHub release from tag `v0.10.9`:
- Title: **Palm Engine 0.10.9 — Architecture Evolution**
- Body: copy `CHANGELOG.md` `[0.10.9]` section
- Attach `dist/*` artifacts if not using CI publish

## Post-release

- [ ] Verify `pip install palmengine[cli]` on clean venv
- [ ] Update any external docs / website
- [ ] Open `[Unreleased]` in `CHANGELOG.md` for next work

## Breaking-change reminders (communicate in release notes)

| 0.9.x habit | 0.10.9 |
|-------------|--------|
| `PalmApp.bootstrap_cli()` | `create_cli_host()` / `ApplicationHost` |
| `status --full` = doctor | `status --full` = detailed **dashboard**; use `doctor` for health |
| Direct `app.list_instances()` in CLI paths | `host.list_instance_views()` via query bus |

Full guide: [MIGRATION-0.10.md](MIGRATION-0.10.md)