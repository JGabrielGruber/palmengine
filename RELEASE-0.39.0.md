# Release checklist — 0.39.0 (bundled: 0.35–0.39 analytics + reactive platform)

**Theme:** Palm **data plane** (Analytics) + **control-plane foundations** (WorkIntent, triggers, journal) + **dashboards** + **system ops datasets** via the Palm provider.

**PyPI version:** **0.39.0**  
**Previous cut:** **0.34.5**  
**Bundles:** 0.35.x · 0.36 · 0.37 foundation · 0.38 foundation · 0.39 foundation · palm system inspect

| Track | Docs |
|-------|------|
| BI / analytics | [VISION-0.35](docs/VISION-0.35.md) |
| Reactive platform | [VISION-0.36](docs/VISION-0.36.md) |
| Dashboards | [ADR-014](docs/adr/014-dashboard-definitions.md) |
| Plan | [plans/2026-07-10-reactive-platform-0.36.md](docs/superpowers/plans/2026-07-10-reactive-platform-0.36.md) |

## Pre-ship

- [x] Version **0.39.0** (`pyproject.toml`, `palm.__version__`)
- [x] CHANGELOG `[0.39.0]`
- [x] RELEASE checklist
- [ ] Tag `v0.39.0`
- [ ] Push + GitHub release
- [ ] Optional PyPI: `just publish`

## Verify

```bash
uv run pytest tests/test_analytics_*.py tests/test_work_*.py tests/test_event_journal.py \
  tests/test_triggers_parse.py tests/test_palm_system_inspect.py -q
uv run python -c "import palm; print(palm.__version__)"
```

## Try

```bash
just palm-server
# http://127.0.0.1:8080/analytics/?dashboard=palm-system
# http://127.0.0.1:8080/analytics/?dashboard=palm-todos
```
