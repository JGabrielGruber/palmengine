"""
Parallel sub-workflow demo — two wizard branches merged with schema validation.

Demonstrates Phase 4 capabilities:

- **Parallel branches** — each runs in an isolated scope + blackboard
- **Sub-workflows** — inline wizard patterns per branch
- **Merge strategy** — ``all`` requires every branch to succeed
- **Parent schema** — merged branch answers validated at completion

```bash
palm wizard start parallel-demo
# alpha → beta (branches interleave input prompts)
```
"""

from __future__ import annotations

from palm.definitions import FlowDefinition, ProcessDefinition

PARALLEL_DEMO_FLOW = FlowDefinition(
    id="flow-parallel-demo",
    name="parallel-demo",
    pattern="parallel",
    state_schema={
        "type": "object",
        "properties": {
            "alpha": {"type": "object"},
            "beta": {"type": "object"},
        },
        "required": ["alpha", "beta"],
    },
    options={
        "merge_strategy": "all",
        "branches": [
            {
                "slug": "alpha",
                "pattern": "wizard",
                "options": {
                    "steps": [
                        {
                            "slug": "alpha",
                            "title": "Alpha",
                            "prompt": "Value for alpha branch?",
                            "state_schema": {"type": "string", "minLength": 1},
                        },
                    ],
                },
                "result_key": "alpha",
            },
            {
                "slug": "beta",
                "pattern": "wizard",
                "options": {
                    "steps": [
                        {
                            "slug": "beta",
                            "title": "Beta",
                            "prompt": "Value for beta branch?",
                            "state_schema": {"type": "string", "minLength": 1},
                        },
                    ],
                },
                "result_key": "beta",
            },
        ],
    },
)

PARALLEL_DEMO_PROCESS = ProcessDefinition(
    id="proc-parallel-demo",
    name="parallel-demo-process",
    flows=[PARALLEL_DEMO_FLOW],
    metadata={
        "example": True,
        "description": "Parallel wizard branches with scoped isolation and merge",
    },
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(PARALLEL_DEMO_FLOW)
    if callable(save_process):
        save_process(PARALLEL_DEMO_PROCESS)