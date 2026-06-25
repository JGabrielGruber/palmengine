# Release checklist — 0.13.13

**Theme:** Provider apps + compositional follow-ups

## Pre-release

- [ ] Version bumped: `pyproject.toml` and `src/palm/__init__.py` → **0.13.13**
- [ ] `CHANGELOG.md` — `[0.13.13]` section complete; `[Unreleased]` empty
- [ ] `just docs-check` passes (README, STATUS, ARCHITECTURE, CHANGELOG, docs surfaces)
- [ ] `just guard-common` passes
- [ ] `just check` passes (lint, typecheck, test-quick, guard-core)
- [ ] `just test-full` green (optional but recommended before PyPI)

## Build & verify

```bash
just release-prep
ls -lh dist/                   # palmengine-0.13.13-*
```

## Tag & publish

```bash
git add -A
git commit -m "Release 0.13.13 — Provider apps + compositional follow-ups"
git tag -a v0.13.13 -m "Palm Engine 0.13.13 — Provider apps + compositional follow-ups"
git push origin master --tags
```

Create GitHub release from tag `v0.13.13` with notes from `CHANGELOG.md` `[0.13.13]`.