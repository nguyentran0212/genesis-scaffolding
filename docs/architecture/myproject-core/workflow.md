# Workflow Architecture

## Overview

The Workflow Engine coordinates step-by-step pipelines involving LLM agents. Each workflow is defined by **inputs**, a sequence of **steps**, and **outputs**. Workflows are declared in YAML manifests — no Python code changes needed to add a new pipeline.

## Key Concepts

### The Blackboard

A shared state object accumulated across step execution. Each step writes its output back to the blackboard; subsequent steps read from it via Jinja2 template references.

```
User input: {"writing_topic": "Python uv"}
Step 1 (agent_outline) → writes {content: "...", file_path: "..."}
Step 2 (agent_drafting) → reads {{ steps.agent_outline.content }} → writes {content: "..."}
```

### Job Directory

Every workflow execution gets an isolated workspace:

```
job_root/
├── input/      ← user-provided files
├── internal/   ← intermediate artifacts between steps
└── output/     ← final workflow artifacts
```

This isolates each run and prevents steps from interfering with each other.

### YAML Manifests

Workflows are YAML files with a defined schema. The engine discovers manifests from configured search paths and validates them before execution.

## Map-Reduce Design

The workflow engine follows a **map-reduce pattern**:

1. **Map tasks** run in parallel, each producing intermediate results written to the blackboard
2. **Reduce tasks** read from the blackboard and assemble final outputs
3. **Projection tasks** handle simple transformations without agent involvement

This pattern keeps steps composable and testable — each task does one thing; the engine composes them into pipelines.

## Task Types

Each task is a Python class with typed inputs and outputs. The engine dispatches to the correct task type based on the `type` field in the manifest.

### `prompt_agent`

Calls an LLM agent with a prompt. The prompt can reference blackboard data via Jinja2. Output is the agent's text response.

### `file` Operations

File tasks read from or write to the job directory. They support reading from `input/`, writing to `output/`, and managing `internal/` artifacts.

### `web_search`

Search the web for a query and return results as structured data.

### `arxiv`

Search ArXiv for papers and retrieve metadata or abstracts.

### `rss_fetch`

Fetch and parse an RSS feed.

### `pdf_to_markdown`

Convert a PDF file to Markdown text.

## Parameter Passing and Static Verification

### Jinja2 Template Resolution

Manifests use Jinja2 to inject blackboard values into task parameters. Before execution, the engine resolves all `{{ ... }}` expressions against the blackboard.

### Static Logic Verification (`_verify_logic`)

The registry performs static verification before any execution begins:

1. It constructs a **mock blackboard** — for each task, it generates a payload from the task's `output_model` Pydantic schema (using default values and empty strings)
2. It attempts to render every Jinja2 expression in the manifest against this mock blackboard
3. If a template references a field that doesn't exist on the mock (e.g., `{{ steps.nonexistent.content }}`), validation fails immediately

This catches broken references at declaration time, not at runtime.

### Runtime Validation

| Layer | When | Purpose |
|---|---|---|
| Manifest schema | On load | YAML structure matches Pydantic schema |
| Static logic | On `engine.run()` call | All Jinja2 references resolve against mock blackboard |
| Runtime input | Per-task, before execution | Task's `params_model` validates the coerced input dict |

## Component Map

| Component | Responsibility |
|---|---|
| **WorkflowEngine** | Executes steps in sequence, resolves templates, updates blackboard, invokes callbacks |
| **WorkflowRegistry** | Discovers manifests, validates schema, performs static logic verification |
| **WorkflowManifest** | Pydantic schema for YAML structure: inputs, steps, outputs, version |
| **Task base class** | Abstract base (`BaseTask`) parameterized by `TParams` and `TOutput` |
| **Built-in tasks** | prompt_agent, file, web_search, arxiv, rss_fetch, pdf_to_markdown |
| **JobContext** | Carries the job root, input/output/internal paths, and blackboard to each task |

## Related Modules

- `myproject_core.workflow.engine` — `WorkflowEngine` and `JobContext`
- `myproject_core.workflow.registry` — `WorkflowRegistry`, manifest discovery and validation
- `myproject_core.workflow.manifest` — `WorkflowManifest` Pydantic schema
- `myproject_core.workflow.tasks` — Built-in task implementations (prompt_agent, file, web_search, arxiv, rss_fetch, pdf_to_markdown)
