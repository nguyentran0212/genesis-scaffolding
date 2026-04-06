# Playbook: Workflow App

**Use when:** The app runs multi-step automated processes, scheduled or on-demand — with or without productivity features or agents.

This playbook is additive on top of the base web app. Apply [core-web-app.md](https://github.com/search?q=repo%3Aanthropics%2Fclaude-code%20path%3Adocs%2Fdeveloper_guides%2Fadaptation%2Fcore-web-app.md&type=code) first, then apply this one.

---

## What to Keep

### Backend
- Everything from the base web app, plus:
- `myproject-core/src/myproject_core/workflow_engine.py`
- `myproject-core/src/myproject_core/workflow_registry.py`
- `myproject-core/src/myproject_core/workflow_tasks/` — workflow task types
- `myproject-core/src/myproject_core/workspace.py`
- `myproject-server/src/myproject_server/routers/workflow.py`
- `myproject-server/src/myproject_server/scheduler.py` — APScheduler for cron jobs

### Frontend
- Workflow, job, and schedule UI pages and components
- Execute workflow buttons and status displays

### Keep or Remove Depending on Need
| Subsystem | Keep when... | Remove when... |
|-----------|-------------|----------------|
| **Productivity** | App needs tasks/projects/journals | App is purely workflow-driven |
| **Memory** | Workflows need to remember context | Not needed |
| **Agents** | Workflows need to delegate to agents | Not needed |

---

## What to Remove

### If Only Workflows (No Productivity, No Agents)
- `myproject-core/src/myproject_core/productivity/`
- `myproject-server/src/myproject_server/routers/productivity.py`
- Productivity frontend components
- `myproject-core/src/myproject_core/agent.py` and `agent_registry.py`
- `myproject-core/src/myproject_core/memory/`
- `myproject-tools/`
- `myproject-core/src/myproject_core/agents/`
- `myproject-server/src/myproject_server/routers/agent.py`
- `myproject-server/src/myproject_server/sse/chatmanager.py`
- Agent and chat frontend components

### If Workflows + Productivity (No Agents)
- `myproject-core/src/myproject_core/agent.py` and `agent_registry.py`
- `myproject-core/src/myproject_core/memory/`
- `myproject-tools/`
- `myproject-core/src/myproject_core/agents/`
- `myproject-server/src/myproject_server/routers/agent.py`
- `myproject-server/src/myproject_server/sse/chatmanager.py`
- Agent and chat frontend components

---

## Where to Add Code

### New Workflow Task Type
Create a new file in `myproject-core/src/myproject_core/workflow_tasks/`.

Follow the pattern of existing task types (e.g., `base_task.py`, `file_read.py`).

Register the task type in `myproject-core/src/myproject_core/workflow_tasks/registry.py`.

### New Tool for Workflows
Tools used by workflow tasks go in `myproject-tools/`.

Follow the [Implementing Tools](https://github.com/search?q=repo%3Aanthropics%2Fclaude-code%20path%3Adocs%2Fdeveloper_guides%2Fextending-the-agent%2Fimplementing-tools.md&type=code) guide.

### New Workflow Definition
Workflow manifests (`.yaml` files) go in `myproject-core/src/myproject_core/workflows/` or a user-managed directory configured in settings.

### Extend the Workflow Frontend
Add pages to `myproject-frontend/app/workflows/`.

---

## What NOT to Do

- Do NOT create a new "workflow runtime" — use `workflow_engine.py` as the orchestrator
- Do NOT create workflow tasks that duplicate what existing tasks do
- Do NOT add workflow logic directly in routers — keep tasks focused and composable
- All other restrictions from [core-web-app.md](https://github.com/search?q=repo%3Aanthropics%2Fclaude-code%20path%3Adocs%2Fdeveloper_guides%2Fadaptation%2Fcore-web-app.md&type=code) apply

---

## Smoke Test

After adaptation:
```bash
uv run pyright .
cd myproject-frontend && pnpm build
```
