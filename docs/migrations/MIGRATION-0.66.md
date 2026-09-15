# Migration — 0.66 Admission sits on capabilities

**Theme:** [VISION-0.66](../vision/closed/VISION-0.66.md) (**closed**) · **ADR:** [035](../adr/035-admission-sits-on-capabilities.md) **Accepted**  
**Map:** [PALM.md](../PALM.md)

Palm is pre-1.0. Theme closed at stamp `0.66.0`. Snapshot fields have defaults. Eyes copy `capabilities`. `require_business_admission` still fail-closes only on `may_run_business`.

## Prefer

| Goal | Use |
|------|-----|
| May business that needs ground run? | `admission.may_run_business` (unchanged) |
| Is this organ here? | `admission.has_capability(name)` / `admission.capabilities` |
| Membership install | Structure definition list + hand. Not the snapshot as walker. |

## Behavior / names that will change

| Was | Now (from 0.66.1) |
|-----|-------------------|
| Snapshot = five fields | Also `capabilities` (installed names, default empty) |
| Organ fact = dig `runtime.structure` or supervisor | Published gate `has_capability` |
| `to_dict()` five keys | Extra key `capabilities` (list). Old readers that pick known keys keep. |

`require_business_admission` still fail-closes only on `may_run_business`. `able` is not this theme.

Dependents that freeze `may_run_business` as the organ list: [VISION-0.67](../vision/closed/VISION-0.67.md) (**closed**) / [SD-020](../../TECH-DEBT.md#sd-020). Costume composted: [VISION-0.68](../vision/closed/VISION-0.68.md) (**closed**). Residual [SD-023](../../TECH-DEBT.md#sd-023).
