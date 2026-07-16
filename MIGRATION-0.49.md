# MIGRATION — 0.49 (composition profiles)

0.49 names the app's two axes apart — *what it's made of* (`CompositionProfile`) vs *where/how it runs*
(`DeploymentProfile`). The renames below establish that vocabulary; `CompositionProfile` itself lands later
in the theme.

## `HostProfile` → `DeploymentProfile` (0.49.1)

The deployment-role profile (`all_in_one` / `worker_only` / `server_only`) is renamed to name its axis. The
class, its presets, role type, and settings helper all move together:

| Before | After |
|---|---|
| `HostProfile` | `DeploymentProfile` |
| `HostProfilePreset` | `DeploymentProfilePreset` |
| `HostRoleName` | `DeploymentRoleName` |
| `host_profile_from_settings()` | `deployment_profile_from_settings()` |

```python
# before
from palm.app import ApplicationHost, HostProfile
host = ApplicationHost(profile=HostProfile.all_in_one())
# after
from palm.app import ApplicationHost, DeploymentProfile
host = ApplicationHost(profile=DeploymentProfile.all_in_one())
```

Unchanged: the `profile=` parameter name, the `roles` property, the `palm.app.host.roles` module, and all
factory methods (`all_in_one` / `master_only` / `worker_only` / `server_only` / `from_preset` / `from_roles`).
Clean rename, no deprecated alias (pre-1.0). Why: it's the *deployment* axis — naming it so keeps it distinct
from the incoming *composition* axis (`CompositionProfile`); a running app is assembled from a
`CompositionProfile` and a `DeploymentProfile`.

## `PalmApp` → `PalmKernel` (0.49.2)

The infrastructure layer (storage + runtime registry + definition loading) is renamed: it isn't "the app",
it's the **substrate** every composition root stands on. The module moves with it.

| Before | After |
|---|---|
| `PalmApp` (class) | `PalmKernel` |
| `palm.app.app` (module) | `palm.app.kernel` |

```python
# before — low-level embedding only; prefer ApplicationHost
from palm.app import PalmApp
kernel = PalmApp().bootstrap()
# after
from palm.app import PalmKernel
kernel = PalmKernel().bootstrap()
```

`ApplicationHost` remains the recommended entrypoint; `PalmKernel` is the infra substrate it (and every other
composition root) builds on. The `palm.app` package name is unchanged.
