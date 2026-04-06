# Scheduled Workflows

This guide explains how to create a workflow and register it to run on a cron schedule.

## Step 1: Create a Workflow Manifest

Place a YAML manifest in your workflow search path (e.g., `working_directory/workflows/`). See the [Workflow Guide](workflow-guide.md) for the manifest schema.

## Step 2: Register the Schedule

Call `POST /schedules/` with the schedule definition:

```bash
curl -X POST http://localhost:8000/schedules/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_id": "workflow_name",
    "cron_expression": "0 9 * * *",
    "timezone": "America/New_York",
    "inputs": {},
    "enabled": true
  }'
```

Required fields:
- `workflow_id`: The identifier of the workflow manifest
- `cron_expression`: Standard cron expression (5 fields)
- `timezone`: IANA timezone string (e.g., `America/New_York`)
- `enabled`: Whether the schedule is active

## Step 3: Monitor Execution

```bash
# Stream live step events
curl -N http://localhost:8000/jobs/<job_id>/stream \
  -H "Authorization: Bearer <token>"

# List all runs for a schedule
curl "http://localhost:8000/jobs/?schedule_id=<schedule_id>" \
  -H "Authorization: Bearer <token>"
```

## Managing Schedules

| Operation | Method | Path |
|---|---|---|
| List schedules | `GET` | `/schedules/` |
| Get schedule | `GET` | `/schedules/{id}` |
| Update schedule | `PATCH` | `/schedules/{id}` |
| Delete schedule | `DELETE` | `/schedules/{id}` |
| Pause/Resume | `PATCH` | `/schedules/{id}` with `enabled: false/true` |
| List job runs | `GET` | `/jobs/?schedule_id={id}` |
| Stream job output | `GET` | `/jobs/{id}/stream` |
