# Developer Guides

These guides help human developers and AI coding agents understand how to extend and modify the codebase. Each guide focuses on a specific task: adding a backend entity, building a frontend page, implementing a new table view, and so on.

For architectural understanding of how the subsystems work, see [scaffolding-overview.md](../architecture/scaffolding-overview.md).

---

## Extending the Backend

| Guide | Description |
|---|---|
| [Adding Entities](extending-the-backend/adding-entities.md) | Adding database entities, models, schemas, FastAPI routers, and dependency injection |
| [Implementing Tools](extending-the-backend/implementing-tools.md) | Implementing a new tool, path validation, ToolResult channels |

## Building the Frontend

| Guide | Description |
|---|---|
| [Frontend Components](building-the-frontend/frontend-components.md) | Server actions, API proxy, integrating new backend entities |
| [Frontend Pages](building-the-frontend/frontend-pages.md) | PageContainer, PageBody, scroll archetypes, layout conventions |
| [Frontend Tables](building-the-frontend/frontend-tables.md) | TanStack Table patterns: sorting, filtering, pagination, bulk actions |

## Automation

| Guide | Description |
|---|---|
| [Workflow Guide](automation/workflow-guide.md) | Writing YAML manifests, blackboard state, invoking workflows, developing new task types |
| [Scheduled Workflows](automation/scheduled-workflows.md) | Creating cron-triggered workflows, APScheduler integration, SSE monitoring |
