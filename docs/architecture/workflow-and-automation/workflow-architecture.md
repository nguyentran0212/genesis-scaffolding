# Workflow Architecture

## Overview

The Workflow Engine is a system for coordinating step-by-step pipelines involving LLM agents. Each workflow is defined by a set of predefined **inputs**, a sequence of **steps**, and a set of final **outputs**.

### Key Architectural Concepts

* **The Blackboard:** A shared state object maintained throughout execution. It stores all initial inputs and the intermediate outputs of every completed step. This allows subsequent steps to consume data produced earlier in the pipeline.
* **Job Directory:** Every workflow execution is provisioned with an automated workspace. This directory structure isolates input files, intermediate states, and final output artifacts.
* **YAML Manifests:** Workflows are defined in YAML files, removing the need to modify Python code to create new processes.
* **Jinja2 Integration:** Manifests support Jinja2 templating for dynamic parameter injection from the blackboard state into step parameters and agent prompts.



### Framework Capabilities

* **Automatic Discovery:** The engine scans and loads all valid manifests from a designated directory.
* **Dual-Layer Validation:** 
  * **Structural:** Ensures the YAML matches the required Pydantic schema.
  * **Logic (Static):** Verifies that all Jinja2 references (e.g., `{{ steps.task_a.content }}`) are valid based on the output models of the referenced tasks before execution begins.
* **Programmatic Execution:** Validated workflows are exposed via a registry for easy invocation.
* **Observability:** Supports asynchronous callbacks to stream progress to terminals, web sockets, or databases.

---

## Validation Layers

The engine maintains reliability through three distinct validation layers:

1. **Manifest Schema Validation:** Uses Pydantic models in `myproject_core.schemas` to verify YAML structure.
2. **Static Logic Validation (`_verify_logic`):** Before execution, the `WorkflowRegistry` generates a "mock blackboard" using the `output_model` of every task. It attempts to render all Jinja2 templates; if a template references a non-existent field, validation fails.
3. **Runtime Validation:**
   * `WorkflowManifest.validate_runtime_inputs` ensures user-provided data matches the expected types (e.g., coercing strings to `Path` objects).
   * Each task's `params_model` validates its specific input dictionary immediately before the task executes.

All core components—including the engine, tasks, and callbacks—are implemented using Python's `asyncio` to ensure high performance and non-blocking I/O during LLM streaming.

---

## Component Map

| Component | Path |
|---|---|
| WorkflowEngine | `myproject-core/src/myproject_core/workflow_engine.py` |
| WorkflowRegistry | `myproject-core/src/myproject_core/workflow_registry.py` |
| WorkflowManifest (schema) | `myproject-core/src/myproject_core/schemas.py` |
| Task base class | `myproject-core/src/myproject_core/workflow_tasks/base.py` |
| Built-in tasks | `myproject-core/src/myproject_core/workflow_tasks/` |

For step-by-step guides on writing workflows, invoking them programmatically, and developing new task types, see [workflow-guide.md](../../guides/automation/workflow-guide.md).
