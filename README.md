# Genesis Scaffolding

<p align="center">
  <img src="assets/logo.png" alt="Genesis Scaffolding Logo" width="100%">
</p>

Genesis Scaffolding is a **general-purpose, capability-stacked application scaffolding** for building production-ready LLM-powered applications.

It provides a modular foundation — Python monorepo, FastAPI backend, NextJS frontend, CLI/TUI — with optional capabilities you can adopt piecemeal: an **agent harness** with tool calls and memory, a **workflow engine**, **cron scheduling**, and a **productivity system** (tasks, projects, journal).

The included demo application is a **personal AI assistant** that uses all capabilities. The scaffolding is designed to be stripped down: build a pure CRUD dashboard, an agent-enabled app, a CLI-only tool, or anything in between.

---

## Project Goals

**A scaffolding for developers** — a layered foundation for building production-ready LLM-powered applications. Pick only the layers you need: Python monorepo, FastAPI backend, agent harness, workflow engine, productivity system, and scheduling. Designed for legibility by humans and AI agents alike.

**A demo application for users** — a fully functional personal AI assistant that demonstrates every capability. Use it as a starting point or strip it to what you need.

**A laboratory for agent research** — an experimental testbed for making small and medium language models more practical, efficient, and safe to run.

---

## Quick Start

```bash
git clone https://github.com/nguyentran0212/genesis-scaffolding
cd genesis-scaffolding
make setup
make dev
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full setup instructions (installing pre-commit hooks, running quality checks, and the pre-merge checklist).

---

## Where to Go Next

| Topic | Doc |
|-------|-----|
| What this project is and isn't | [docs/project_goals.md](docs/project_goals.md) |
| Architecture overview | [docs/architecture/scaffolding-overview.md](docs/architecture/scaffolding-overview.md) |
| How to contribute | [CONTRIBUTING.md](CONTRIBUTING.md) |
| Running in dev / prod / Docker | [docs/developer_guides/development-workflow.md](docs/developer_guides/development-workflow.md) |
| How to adapt the scaffolding | [docs/developer_guides/adaptation/README.md](docs/developer_guides/adaptation/README.md) |

