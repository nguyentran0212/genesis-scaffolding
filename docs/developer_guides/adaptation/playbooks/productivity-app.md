# Playbook: Productivity App

**Use when:** The app needs tasks, projects, journals, or calendar — with or without agents.

This playbook is additive on top of the base web app. Apply [core-web-app.md](https://github.com/search?q=repo%3Aanthropics%2Fclaude-code%20path%3Adocs%2Fdeveloper_guides%2Fadaptation%2Fcore-web-app.md&type=code) first, then apply this one.

---

## What to Keep

### Backend
- Everything from the base web app, plus:
- `myproject-core/src/myproject_core/productivity/` — models, service, DB
- `myproject-server/src/myproject_server/routers/productivity.py`

### Frontend
- Everything from the base web app, plus:
- Productivity UI components (task table, project table, journal, calendar)
- Dashboard page with pinned productivity items

### Remove
- `myproject-core/src/myproject_core/agent.py` and `agent_registry.py`
- `myproject-core/src/myproject_core/memory/`
- `myproject-core/src/myproject_core/workflow_engine.py` and `myproject-core/src/myproject_core/workflow_registry.py`
- `myproject-core/src/myproject_core/workflow_tasks/`
- `myproject-core/src/myproject_core/workspace.py`
- `myproject-server/src/myproject_server/routers/agent.py`
- `myproject-server/src/myproject_server/routers/workflow.py`
- `myproject-server/src/myproject_server/sse/chatmanager.py`
- `myproject-tools/`
- `myproject-core/src/myproject_core/agents/`

### Frontend — Remove
- Chat UI components and pages related to agents
- Workflow/job/schedule UI pages

---

## Where to Add Code

### New Productivity Entity
Add models to `myproject-core/src/myproject_core/productivity/models.py`.

Add service methods to `myproject-core/src/myproject_core/productivity/service.py`.

Add router endpoints to `myproject-server/src/myproject_server/routers/productivity.py`.

### Extend the Productivity Frontend
Add components to the appropriate feature directory in `myproject-frontend/components/`.

---

## What NOT to Do

- Do NOT add productivity entities as agent tools — productivity is its own subsystem
- Do NOT create separate "productivity API client" packages — use the existing service layer
- All other restrictions from [core-web-app.md](https://github.com/search?q=repo%3Aanthropics%2Fclaude-code%20path%3Adocs%2Fdeveloper_guides%2Fadaptation%2Fcore-web-app.md&type=code) apply

---

## Smoke Test

After adaptation:
```bash
uv run pyright .
cd myproject-frontend && pnpm build
```
