# Scheduled Workflows

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

## 5. Timezone Strategy
To ensure "9:00 AM" means the same thing regardless of server location:
* All timestamps are stored as **Naive UTC** in the database.
* Frontend parsing (via `date-utils.ts`) appends the `Z` suffix to force browser-side UTC interpretation before converting to local display time.
* Cron triggers use the explicitly stored `timezone` string (e.g., `Australia/Adelaide`) to calculate the next execution offset.
