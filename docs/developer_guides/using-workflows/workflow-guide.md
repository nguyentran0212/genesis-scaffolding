# Workflow Guide

This guide covers how to write, invoke, and extend the workflow system.

## Writing a Workflow Manifest

Place a YAML manifest in your workflow search path (e.g., `working_directory/workflows/`). It is automatically discovered and validated.

### Manifest Schema

```yaml
name: "Sample Workflow"
version: "1.0"

inputs:
  input_param:
    type: "string"
    description: "Description of the input"
    default: "default value"

steps:
  - id: "step_one"
    type: "prompt_agent"
    params:
      prompt: "Your prompt with {{ inputs.input_param }}"

outputs:
  output_key:
    description: "Description of output"
    value: "{{ steps.step_one.content }}"
```

### The Blackboard

During execution, the engine populates a state object. References in the YAML resolve against this structure:

```
inputs.*         — user-provided inputs
steps.{id}.*    — output fields from a previous step
```

## Invoking a Workflow Programmatically

```python
wm = WorkspaceManager(settings)
reg = WorkflowRegistry(settings)
engine = WorkflowEngine(wm)

manifest = reg.get_workflow("workflow_name")
user_data = {"input_key": "value"}

result = await engine.run(manifest, user_data, callbacks=[...])
```

**WorkflowRegistry**: Handles discovery, schema validation, and logic checking.
**WorkflowEngine**: Handles step-by-step execution, template resolution, and blackboard updates.

## Developing New Workflow Step Types

Each task type requires three components defined in `myproject_core.workflow_tasks`:

1. **TaskParams**: A Pydantic model defining the task's allowed input parameters
2. **TaskOutput**: A Pydantic model defining the data the task will write back to the blackboard
3. **TaskClass**: A subclass of `BaseTask[TParams, TOutput]` implementing the `run()` logic

## Validation Layers

The workflow engine has three validation layers:

| Layer | When | Purpose |
|---|---|---|
| **Manifest Schema** | On load | YAML structure matches Pydantic schema |
| **Static Logic** | On `engine.run()` | All Jinja2 references resolve against mock blackboard |
| **Runtime Input** | Per-task, before execution | Task's `params_model` validates the coerced input dict |
