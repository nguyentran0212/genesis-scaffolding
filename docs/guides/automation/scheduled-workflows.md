# Creating a Scheduled Workflow

This guide explains how to create a workflow and register it to run on a cron schedule.

For the scheduling architecture, see [scheduled-workflows.md](../../architecture/workflow-and-automation/scheduled-workflows.md).

---

## Step 1: Create a Workflow Manifest

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

For the workflow manifest schema, see [workflow-architecture.md](../../architecture/workflow-and-automation/workflow-architecture.md).

## Step 2: Register the Schedule

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

## Step 3: Monitor Execution

```bash
# Stream live step events
curl -N http://localhost:8000/jobs/<job_id>/stream \
  -H "Authorization: Bearer <token>"

# List all runs for a schedule
curl "http://localhost:8000/jobs/?schedule_id=<schedule_id>" \
  -H "Authorization: Bearer <token>"
```
