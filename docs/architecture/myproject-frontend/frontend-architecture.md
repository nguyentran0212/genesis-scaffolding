# Frontend Architecture

## Overview

The frontend is a NextJS web application using the App Router. It handles server-side rendering and is deployed separately from the Python backend. Users interact with the agent and productivity system through this UI.

## Codebase Organization

```
myproject-frontend/
├── app/                    # Next.js App Router pages and layouts
│   ├── actions/            # Server Actions (data mutations, API calls)
│   ├── api/[...proxy]/     # API proxy route (forwards to FastAPI)
│   ├── dashboard/          # Dashboard pages (projects, tasks, journals, agents, etc.)
│   ├── login/              # Login page
│   └── register/           # Registration page
├── components/
│   ├── auth/               # Auth components (login form, logout button)
│   ├── chat/               # Chat UI components
│   ├── dashboard/          # Dashboard-specific components
│   │   ├── shared/data-table/   # TanStack Table engine and shared table components
│   │   ├── tasks/          # Task-specific components
│   │   ├── projects/       # Project-specific components
│   │   ├── journals/       # Journal-specific components
│   │   └── ...             # Other domain-specific components
│   └── ui/                 # Shadcn UI component library
├── lib/                    # Client-side utilities
│   ├── api-client.ts       # Typed API client for server-side fetch
│   ├── auth.ts             # Auth utilities
│   ├── date-utils.ts       # Date formatting helpers
│   └── ...
├── types/                  # TypeScript interface definitions
│   ├── api.ts              # General API types
│   ├── auth.ts             # Auth types
│   ├── chat.ts             # Chat message types
│   ├── productivity.ts     # Task, project, journal types
│   └── ...
└── hooks/                  # React hooks
```

## App Router

The frontend uses Next.js App Router (`app/` directory). Routes are defined by the file system structure under `app/`. Each route can have:

- `page.tsx` — The page component (server or client)
- `layout.tsx` — A shared layout wrapping child pages
- `loading.tsx` — A loading state for the route

### Dashboard Routes

The main application lives under `app/dashboard/`:

| Path | Description |
|---|---|
| `app/dashboard/page.tsx` | Dashboard home |
| `app/dashboard/tasks/` | Task list and management |
| `app/dashboard/projects/` | Project management |
| `app/dashboard/journals/` | Journal entries |
| `app/dashboard/agents/` | Agent configuration |
| `app/dashboard/chats/` | Chat history |
| `app/dashboard/jobs/` | Workflow job monitoring |
| `app/dashboard/workflows/` | Workflow management |
| `app/dashboard/schedules/` | Schedule management |
| `app/dashboard/memory/` | Agent memory viewer |
| `app/dashboard/sandbox/` | File sandbox browser |
| `app/dashboard/settings/` | User settings |
| `app/dashboard/calendar/` | Calendar view |

## Server Actions

Form submissions and data mutations run server-side via NextJS Server Actions in `app/actions/`. Server Actions are async functions that execute on the server and can return data to client components.

Example server action pattern:

```typescript
// app/actions/tasks.ts
'use server'
import { apiFetch } from "@/lib/api-client";
import { revalidatePath } from "next/cache";

export async function getTasksAction() {
  const res = await apiFetch(`/productivity/tasks/`);
  if (!res.ok) throw new Error("Failed to fetch tasks");
  return res.json();
}

export async function createTaskAction(data: TaskCreateInput) {
  const res = await apiFetch(`/productivity/tasks/`, {
    method: 'POST',
    body: JSON.stringify(data),
  });
  revalidatePath('/dashboard/tasks');
  return res.json();
}
```

## API Proxy

All browser requests to FastAPI are routed through `app/api/[...proxy]/route.ts`. This proxy forwards requests to the FastAPI backend, ensuring credentials and API keys are never exposed to the client browser.

The `apiFetch` utility in `lib/api-client.ts` is the standard way to make API calls — it handles the proxy path and authentication headers.

## Dashboard Layout

The dashboard uses a shared layout with a collapsible sidebar (`app/dashboard/layout.tsx`). The layout structure:

```
<SidebarProvider>
  <Sidebar>              # Navigation sidebar with grouped menu items
  <div>
    <header>            # Top bar with sidebar trigger and dynamic header
    <main>              # Page content area
  </div>
</SidebarProvider>
```

Navigation is organized into groups: **Productivity**, **Interaction**, **Automation**, and **Knowledge**.

## Page Layout System

Dashboard pages use two helper components to ensure consistent layout and prevent scroll issues:

- **`PageContainer`** (`components/dashboard/page-container.tsx`) — Constrains width and manages scroll behavior per variant
- **`PageBody`** (`components/dashboard/page-container.tsx`) — Provides standard padding and spacing

See [frontend-pages.md](frontend-pages.md) and [frontend-components.md](frontend-components.md) for detailed usage.

## Data Tables

TanStack Table is used for listing and filtering productivity entities. The implementation spans two directories:

- **`components/dashboard/shared/data-table/`** — Shared table engine (`DataTable`, `DataTableColumnHeader`, pagination controls)
- **`components/dashboard/[entity]/`** — Entity-specific column definitions and table orchestrators

See [frontend-tables.md](frontend-tables.md) for detailed usage patterns.

## Chat UI

The chat interface communicates with the backend via Server-Sent Events (SSE) at `/api/chats/{id}/stream`. For full streaming architecture details, see [myproject-server/sse-streaming.md](../myproject-server/sse-streaming.md).

## Tech Stack

- **Framework**: Next.js (App Router)
- **UI Components**: Shadcn UI
- **Icons**: Lucide-react
- **Styling**: Tailwind CSS / PostCSS
- **Tables**: TanStack Table
- **Forms**: React Hook Form + Zod

## Related Modules

- `myproject_frontend/app/` — App Router pages and layouts
- `myproject_frontend/app/actions/` — Server Actions
- `myproject_frontend/app/api/[...proxy]/` — API proxy route
- `myproject_frontend/components/dashboard/` — Dashboard components including page-container
- `myproject_frontend/components/dashboard/shared/data-table/` — TanStack Table engine
- `myproject_frontend/lib/api-client.ts` — API client utility
