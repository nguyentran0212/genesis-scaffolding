# Automation & Scheduling Architecture

Genesis Scaffolding includes a built-in automation engine for recurring tasks, designed to run independently of the API request lifecycle.

## 1. The Persistence Layer
Automations are stored in the `workflow_schedule` table. Unlike manual jobs, a Schedule acts as a "Job Factory."
* **Context Preservation**: At creation time, the API captures the user's current absolute sandbox path and IANA timezone. This allows the background worker to resolve relative file paths without access to FastAPI dependency injection.

## 2. The Scheduler Manager
We utilize `APScheduler` (AsyncIOScheduler) integrated into the FastAPI lifespan:
* **Lifespan Sync**: On server startup, the `SchedulerManager` hydrates the in-memory schedule from the SQLite database.
* **Real-time Mutation**: CRUD operations on schedules trigger immediate updates to the `AsyncIOScheduler` instance, allowing "Pause/Resume" and "Edit Frequency" to take effect without server restarts.

## 3. Execution Flow
1. **Trigger**: The Cron expression hits based on the stored IANA Timezone.
2. **Spawn**: The manager creates a `WorkflowJob` record (status: `PENDING`) and links it to the `schedule_id`.
3. **Resolve**: The manager uses the stored `user_directory` to expand any file-based workflow inputs.
4. **Execute**: The `WorkflowEngine` is invoked with the prepared inputs.
5. **Traceability**: All results, logs, and artifacts are linked back to the parent Schedule, visible via the `GET /jobs?schedule_id=...` filter.

## 4. API Endpoints

The schedules and jobs routers expose the following endpoints:

### Schedules (`/schedules`)

| Method | Path | Description |
|---|---|---|
| GET | `/schedules/` | List all schedules for current user |
| POST | `/schedules/` | Create a new schedule (upserts into APScheduler if enabled) |
| GET | `/schedules/{schedule_id}` | Get schedule detail |
| PATCH | `/schedules/{schedule_id}` | Update schedule (syncs cron trigger with APScheduler) |
| DELETE | `/schedules/{schedule_id}` | Remove from DB and APScheduler |

### Jobs (`/jobs`)

| Method | Path | Description |
|---|---|---|
| POST | `/jobs/` | Submit a workflow job (runs in background) |
| GET | `/jobs/` | List jobs (supports `?schedule_id=` filter) |
| GET | `/jobs/{job_id}` | Get job detail + step status |
| GET | `/jobs/{job_id}/stream` | SSE stream for step events (`step_start`, `step_completed`, `step_failed`) |
| GET | `/jobs/{job_id}/output` | List files in job's output directory |
| GET | `/jobs/{job_id}/output/{path}` | Download a specific output file |

## 5. How to Create a New Scheduled Workflow

### Step 1: Create a Workflow Manifest

Place a YAML manifest in your workflow search path (e.g., `working_directory/workflows/`):

```yaml
# greeting_workflow.yaml
name: "Daily Greeting"
description: "Send a daily greeting email"

steps:
  - id: fetch_tasks
    type: agent_projection
    agent: max
    prompt: "List all tasks due today from the task system"

  - id: compose_email
    type: agent_map
    agent: max
    input: "{{ steps.fetch_tasks.output }}"
    prompt: "Write a friendly email summarizing these tasks"
```

### Step 2: Register the Schedule

```bash
curl -X POST http://localhost:8000/schedules/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "greeting_workflow",
    "cron_expression": "0 9 * * *",
    "timezone": "America/New_York",
    "inputs": {},
    "enabled": true
  }'
```

### Step 3: Monitor Execution

```bash
# Stream live step events
curl -N http://localhost:8000/jobs/<job_id>/stream \
  -H "Authorization: Bearer <token>"

# List all runs for a schedule
curl "http://localhost:8000/jobs/?schedule_id=<schedule_id>" \
  -H "Authorization: Bearer <token>"
```

---

## 6. Timezone Strategy
To ensure "9:00 AM" means the same thing regardless of server location:
* All timestamps are stored as **Naive UTC** in the database.
* Frontend parsing (via `date-utils.ts`) appends the `Z` suffix to force browser-side UTC interpretation before converting to local display time.
* Cron triggers use the explicitly stored `timezone` string (e.g., `Australia/Adelaide`) to calculate the next execution offset.
