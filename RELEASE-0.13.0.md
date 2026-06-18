# Release checklist — 0.13.0

**Theme:** Wizard Experience — REST + Explorer workspace + collection UI

## Pre-release

- [ ] Version bumped: `pyproject.toml` and `src/palm/__init__.py` → **0.13.0**
- [ ] `CHANGELOG.md` — `[0.13.0]` section complete; `[Unreleased]` empty
- [ ] `just docs-check` passes (README, STATUS, ARCHITECTURE, CHANGELOG, docs surfaces)
- [ ] `just check` passes (lint, typecheck, test-quick, guard-core)
- [ ] `just test-full` green (optional but recommended before PyPI)
- [ ] `just docs-build` — Tailwind CSS rebuilt if `docs/` changed
- [ ] Review [EXPLORER-WIZARD.md](EXPLORER-WIZARD.md) and [docs/VISION-0.13.md](docs/VISION-0.13.md)

## Build & verify

```bash
just release-prep
ls -lh dist/                   # palmengine-0.13.0-*
```

## TestPyPI (optional)

```bash
export TEST_PYPI_TOKEN=...
just publish-test
pip install -i https://test.pypi.org/simple/ 'palmengine[cli]==0.13.0'
palm version --full
```

## Tag & publish

```bash
git add -A
git commit -m "Release 0.13.0 — Wizard Experience"
git tag -a v0.13.0 -m "Palm Engine 0.13.0 — Wizard Experience"
git push origin master --tags
```

Create GitHub release from tag `v0.13.0`:
- Title: **Palm Engine 0.13.0 — Wizard Experience**
- Body: copy `CHANGELOG.md` `[0.13.0]` section

## Post-release

- [ ] `pip install palmengine[cli]==0.13.0` smoke test
- [ ] Update `STATUS.md` shipping note if needed
- [ ] Announce: `/v1/wizards`, Explorer collection UI, phase refactor docs

## Highlights for release notes

- First-class **`/v1/wizards`** REST API (instance-keyed submit, status, input, backtrack)
- **Explorer wizard workspace** with HTMX partial updates
- **Collection step UI** — overview card, add/edit/remove, field draft, remove confirm
- Wizard **phase modularization** under `palm/patterns/wizard/phases/`
- Guide: [EXPLORER-WIZARD.md](EXPLORER-WIZARD.md)