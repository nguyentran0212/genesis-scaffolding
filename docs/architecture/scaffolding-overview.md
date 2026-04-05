# Genesis Scaffolding — Project Overview

Genesis Scaffolding is a **general-purpose, capability-stacked application scaffolding** for building production-ready LLM-powered applications. Rather than being a single-purpose tool, it provides a modular foundation where developers pick and choose which capabilities to use.

For the project's purpose statement, see [docs/project_goals.md](../project_goals.md).

---

## The Layered Architecture

The scaffolding is organized in layers. Developers choose which layers to adopt based on their needs:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (Optional)                       │
│         NextJS — App Router, Server Actions, Components          │
│         for dashboard layout, data tables, and agent UI          │
├─────────────────────────────────────────────────────────────────┤
│                     Python Monorepo (Core)                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  myproject   │  │ myproject    │  │   myproject-server   │  │
│  │  -core       │  │ -cli         │  │   - FastAPI          │  │
│  │  -tools      │  │ -tui         │  │   - Auth             │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                   Available Capabilities                         │
│  • Agent Harness     • Workflow Engine     • Productivity       │
│  • Scheduling         • Memory System       • Tool System       │
└─────────────────────────────────────────────────────────────────┘
```

### Platform Layer

- **Python Monorepo (uv workspaces)** — Sub-packages can see and import from each other following uv's workspace conventions. Single shared `.venv`, single `uv.lock`.
- **FastAPI Backend** — REST API with password-based authentication, SSE streaming, already configured to work with the frontend.
- **NextJS Frontend** — App routing, server-side actions, proxy for browser → server-side fetching, dashboard layout components, data table system.
- **CLI/TUI** — Typer-based CLI, Textual TUI (CLI is functional; TUI is a stub for future development).

### Capability Layer

Developers can adopt any subset:

| Capability | Description |
|---|---|
| **Agent Harness** | Interactive agent with tool calls, clipboard-based token optimization, persistent memory, multi-backend LLM support (OpenAI-compatible via LiteLLM, Claude via Anthropic SDK). Agent definitions loaded from markdown files. Sandboxed working directories. |
| **Workflow Engine** | Map-reduce architecture. Workflow *tasks* are Python classes; workflow *manifests* are YAML files. Supports agent_map, agent_reduce, agent_projection, file operations, arxiv, web search. |
| **Scheduling** | Cron-based job scheduling attached to workflows. Multi-user mode only. |
| **Productivity System** | Tasks, Projects, Calendar appointments, Journal entries. Fully accessible to agents via tool calls when authorized. |
| **Tool System** | BaseTool ABC for writing Python tools. Multi-channel results (text + files + DB entities). Registry of 30+ built-in tools. |
| **Memory System** | EventLog (append-only facts) + TopicalMemory (revisable knowledge with supersession chain). FTS5 full-text search. |

---

## Example Applications

The scaffolding is deliberately flexible. Here are some applications developers could build:

### 1. Personal AI Assistant (uses ALL capabilities)
The included demo app uses every capability: agent harness, workflows, scheduling, productivity system, multi-user server, configurable LLM providers.

### 2. Pure CRUD Dashboard
Forego all agent/workflow stuff. Use the FastAPI backend + NextJS frontend to build a dashboard for managing infrastructure, content, or any data — leveraging only the auth, API, and frontend component layers.

### 3. Agent-Enabled Specialized App
Keep the agent harness, workflows, and tool system. Add specialized agents and custom tools for a specific domain (e.g., code review, data analysis, customer support).

### 4. CLI-Only App
Forego the frontend entirely. Extend the CLI with new commands using Typer, leveraging the backend Python code as a library.

### 5. Custom Frontend with Shared Backend
Completely redesign the frontend's look and feel, keeping server actions, the dashboard layout system, and utility components. The backend API remains the same.

---

## The Demo App: Personal AI Assistant

As a demonstration of the scaffolding's capabilities, Genesis Scaffolding includes a fully functional **personal AI assistant** application. This demonstrates:

- Running in **multi-user server mode** with per-user YAML config overrides merged into a server-wide config
- **Agent personas** (loaded from markdown files) selectable by users
- **Deterministic workflows** triggered on-demand or on a **cron schedule**
- **Productivity management** — tasks, projects, calendar, journal — accessible to agents
- **Multiple LLM provider support** — users configure their own providers from the frontend
- **Long-running task support** via the workflow engine

This demo app is the **starting point**, not the ceiling. Developers adopting the scaffolding are encouraged to strip out what they don't need and build on top of what they do.

---

## Design Principles

The codebase is designed to be understandable and maintainable by both human developers and LLM-based coding agents:

- **Clarity over Abstraction** — Thin architecture close to the logic. No unnecessary layers or generics obscuring implementation.
- **Well-defined Dependencies** — No circular dependencies. Every package and module has a narrowly defined purpose.
- **Canonical Tooling** — Modern, standard libraries: `uv`, `Pydantic`, `pydantic-settings`, `Typer`, `Textual`, `FastAPI`, `litellm`, `sqlmodel`, `NextJS`, `TanStack Table`.
- **Pick Your Complexity** — Start with what you need. Add capabilities as your application grows.

---

## Architecture Documentation

Detailed architecture documentation covers how each subsystem works and the key design decisions behind them:

### How Agents Work

| Document | Description |
|---|---|
| [agent-integration](how-agents-work/agent-integration.md) | End-to-end flow: FastAPI → Agent → SSE → Frontend |
| [agent-loop](how-agents-work/agent-loop-architecture.md) | Internal agent execution loop: step, turns, clipboard injection, loop detection |
| [agent-clipboard](how-agents-work/agent-clipboard.md) | Token optimization via clipboard + TTL decay |
| [memory-system](how-agents-work/memory-system.md) | EventLog, TopicalMemory, FTS5 full-text search |
| [prompt-system](how-agents-work/prompt-system.md) | Fragment-based system prompt assembly |
| [llm-provider-abstraction](how-agents-work/llm-provider-abstraction.md) | Provider-agnostic LLM interface: LiteLLM, Anthropic SDK, streaming callbacks |
| [agent-registry](how-agents-work/agent-registry.md) | Loading agents from markdown, YAML frontmatter schema, CRUD via registry |
| [productivity-system](platform/productivity-system.md) | Tasks, Projects, Journals, calendar appointments — models, tools, clipboard integration |

### Workflow and Automation

| Document | Description |
|---|---|
| [workflow-architecture](workflow-and-automation/workflow-architecture.md) | Blackboard pattern, YAML manifests, map-reduce tasks |
| [scheduled-jobs](workflow-and-automation/scheduled-jobs.md) | APScheduler integration for cron jobs |

### Tools and Extensibility

| Document | Description |
|---|---|
| [tool-architecture](tools-and-extensibility/tool-architecture.md) | BaseTool ABC, multi-channel ToolResult, tool registry |

### Project Structure

| Document | Description |
|---|---|
| [monorepo-structure](monorepo-structure.md) | uv workspace layout, 5 packages, import conventions, dependency management |

### Platform Layer

Detailed documentation on the server-side architecture, configuration system, and how core and server interact:

| Document | Description |
|---|---|
| [platform-layer](platform/platform-layer.md) | FastAPI app, lifespan, dependency injection, three-database architecture, SSE streaming, scheduler, all REST routers |
| [productivity-system](platform/productivity-system.md) | Tasks, Projects, Journals, calendar appointments — models, tools, clipboard integration |

### Developer Guides

Step-by-step guides for extending and modifying the codebase:

| Document | Description |
|---|---|
| [extending the backend](guides/extending-the-backend/server-and-database.md) | Adding entities, models, schemas, FastAPI routers |
| [building the frontend](guides/building-the-frontend/components.md) | Server actions, API proxy, component conventions |
| [frontend pages](guides/building-the-frontend/pages.md) | PageContainer, PageBody, scroll archetypes |
| [frontend tables](guides/building-the-frontend/tables.md) | TanStack Table patterns, sorting, filtering |

---

## Quick Reference: Package Map

| Package | Purpose |
|---|---|
| `myproject-core` | Shared logic: agent, clipboard, memory, workflows, prompts, LLM abstraction, config |
| `myproject-tools` | 30+ built-in tools: file ops, productivity, memory, web, PDF, arxiv |
| `myproject-cli` | Typer CLI entry point |
| `myproject-tui` | Textual TUI (stub) |
| `myproject-server` | FastAPI REST API, auth, SSE streaming |
| `myproject-frontend` | NextJS frontend (separate repo structure) |

> **Note on naming:** Project names use hyphens (`myproject-core`), but Python packages use underscores. Always import with underscores: `import myproject_core`.
