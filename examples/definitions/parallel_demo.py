"""
Parallel sub-workflow demo — schemas, scoped branches, and merge validation.

Demonstrates Phase 4 + Phase 5 CLI visibility:

- **Parallel branches** — each runs in an isolated scope + blackboard
- **Multi-step sub-workflows** — two wizard steps per branch
- **Per-step schemas** — integer age on alpha, string role on beta
- **Parent schema** — merged branch answers validated at completion
- **Merge strategy** — ``all`` requires every branch to succeed

```bash
palm flow start parallel-demo
# or: palm start parallel-demo
# Branches interleave prompts — watch REPL prompt for @parallel:<branch>
palm doctor                   # active branch + schema context
palm status <instance_id>     # branch progress + scope path
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
            "alpha": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "age": {"type": "integer", "minimum": 1},
                },
                "required": ["name", "age"],
            },
            "beta": {
                "type": "object",
                "properties": {
                    "team": {"type": "string", "minLength": 1},
                    "role": {"type": "string", "enum": ["developer", "designer", "pm"]},
                },
                "required": ["team", "role"],
            },
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
                            "slug": "name",
                            "title": "Alpha — Name",
                            "prompt": "Contributor name for alpha branch?",
                            "state_schema": {"type": "string", "minLength": 1},
                        },
                        {
                            "slug": "age",
                            "title": "Alpha — Age",
                            "prompt": "Contributor age (integer)?",
                            "state_schema": {"type": "integer", "minimum": 1},
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
                            "slug": "team",
                            "title": "Beta — Team",
                            "prompt": "Team name for beta branch?",
                            "state_schema": {"type": "string", "minLength": 1},
                        },
                        {
                            "slug": "role",
                            "title": "Beta — Role",
                            "prompt": "Role (developer, designer, or pm)?",
                            "field_type": "choice",
                            "choices": ["developer", "designer", "pm"],
                            "state_schema": {
                                "type": "string",
                                "enum": ["developer", "designer", "pm"],
                            },
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
        "description": "Parallel wizard branches with schemas, scopes, and merge",
    },
)


def register_definitions(repository: object) -> None:
    save_flow = getattr(repository, "save_flow", None)
    save_process = getattr(repository, "save_process", None)
    if callable(save_flow):
        save_flow(PARALLEL_DEMO_FLOW)
    if callable(save_process):
        save_process(PARALLEL_DEMO_PROCESS)