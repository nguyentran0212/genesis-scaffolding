# Adapting the Scaffolding

This section covers how to adapt the Genesis Scaffolding to build a different application.

---

## How It Works

The scaffolding provides a **base web app** and **independent extensions**:

| Component | Description |
|-----------|-------------|
| **Base: Core Web App** | FastAPI backend + NextJS frontend + login + dashboard + CRUD entities |
| **Extension: Productivity** | Tasks, projects, journals, calendar |
| **Extension: Workflows & Scheduling** | Multi-step automated processes, scheduled jobs |
| **Extension: Agents** | AI agent loop, tool registry, agent definitions, chat UI |

Extensions are **additive and independent**. You can combine any of them.

---

## Decision Process

When asked to adapt the scaffolding for a new application:

1. [Read the decision process](decision-process.md) — Follow this before touching any code
2. Select extensions based on user needs
3. Follow the relevant playbook(s)
4. Verify with smoke tests

---

## Playbooks

| Playbook | Use when |
|----------|----------|
| [core-web-app.md](core-web-app.md) | Web UI + FastAPI only. No agents, no workflows, no productivity. |
| [productivity-app.md](playbooks/productivity-app.md) | Tasks, projects, journals, calendar |
| [workflow-app.md](playbooks/workflow-app.md) | Multi-step automated processes, scheduled jobs |
| [full-agent-app.md](playbooks/full-agent-app.md) | Everything — the current demo app |

---

## Principles

Review [principles.md](principles.md) for the rules that apply to all adaptation work. The key rules:

- Extend where code already lives — don't create new packages without a real need
- No unnecessary abstraction — if one function suffices, don't add a registry
- Trim don't hide — remove unused subsystems
- Ask before guessing — confirm capabilities with the user before proceeding
