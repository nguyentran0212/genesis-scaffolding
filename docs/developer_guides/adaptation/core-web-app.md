# Playbook: Base Web App

**Use when:** The app needs a web UI backed by a FastAPI server. No agents, no workflows, no productivity features.

---

## What to Keep

### Backend
- `myproject-core/` — Core utilities, configs, schemas, LLM client (if you need it later)
- `myproject-server/` — FastAPI server, routers, auth, database models

### Frontend
- `myproject-frontend/` — NextJS app, pages, components, API client

### Remove
- `myproject-core/src/myproject_core/agent.py` and `agent_registry.py`
- `myproject-core/src/myproject_core/productivity/` — productivity models, service, DB
- `myproject-core/src/myproject_core/memory/` — memory subsystem
- `myproject-core/src/myproject_core/workflow_engine.py` and `myproject-core/src/myproject_core/workflow_registry.py`
- `myproject-core/src/myproject_core/workflow_tasks/`
- `myproject-core/src/myproject_core/workspace.py`
- `myproject-server/src/myproject_server/routers/productivity.py`
- `myproject-server/src/myproject_server/routers/agent.py`
- `myproject-server/src/myproject_server/routers/workflow.py`
- `myproject-server/src/myproject_server/sse/chatmanager.py`
- `myproject-tools/` — all tools
- `myproject-core/src/myproject_core/agents/` — all agent definitions

### Frontend — Remove
- Chat UI components and pages related to agents
- Workflow/job/schedule UI pages
- Productivity UI components (task, project, journal, calendar)

---

## Where to Add Code

### New Backend Entity
Follow the [Adding Entities](https://github.com/search?q=repo%3Aanthropics%2Fclaude-code%20path%3Adocs%2Fdeveloper_guides%2Fextending-the-server%2Fadding-entities.md&type=code) guide.

Add models to `myproject-core/src/myproject_core/schemas.py` or a new module in `myproject-core/src/myproject_core/`.

Add routers to `myproject-server/src/myproject_server/routers/`. Register in `myproject-server/src/myproject_server/main.py`.

### New Frontend Page
Follow the [Frontend Pages](https://github.com/search?q=repo%3Aanthropics%2Fclaude-code%20path%3Adocs%2Fdeveloper_guides%2Fextending-the-frontend%2Ffrontend-pages.md&type=code) guide.

Add to `myproject-frontend/app/`.

---

## What NOT to Do

- Do NOT create a new Python package outside of `myproject-core/` or `myproject-server/` for domain logic
- Do NOT create new registries or abstraction layers — add directly to existing routers and services
- Do NOT import from `myproject-tools/` or `myproject-core/agents/`

---

## Smoke Test

After adaptation:
```bash
uv run pyright .
cd myproject-frontend && pnpm build
```
