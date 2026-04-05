# Workflow Guide

This guide covers how to write, invoke, and extend the workflow system.

For the workflow architecture, see [workflow-architecture.md](../../architecture/workflow-and-automation/workflow-architecture.md).

---

## Writing a Workflow Manifest

Place a YAML manifest in your workflow search path (e.g., `working_directory/workflows/`). It is automatically discovered and validated.

### Manifest Schema

```yaml
name: "Sample Multi-Step Agent Workflow"
description: "A simple multi-step workflow to test agent integration."
version: "1.0"

inputs:
  writing_topic:
    type: "string"
    description: "Topic for the agent."
    default: "Python monorepo."
  content_length:
    type: "int"
    description: "Target word count."
    default: 500

steps:
  - id: "agent_outline"
    type: "prompt_agent"
    params:
      prompt: "Create an outline for {{ inputs.writing_topic }}."
      output_filename: "agent_outline.md"

  - id: "agent_drafting"
    type: "prompt_agent"
    params:
      prompt: "Write a draft based on this outline: {{ steps.agent_outline.content }}"
      output_filename: "agent_draft.md"

outputs:
  blog_post:
    description: "The final edited version."
    value: "{{ steps.agent_drafting.content }}"
```

### The Blackboard

During execution, the engine populates a state object. References in your YAML resolve against this structure:

```json
{
  "inputs": {
    "writing_topic": "...",
    "content_length": 500
  },
  "steps": {
    "agent_outline": {
      "content": "...",
      "file_path": "..."
    }
  }
}
```

---

## Invoking a Workflow Programmatically

```python
async def main():
    # 1. Setup Infrastructure
    wm = WorkspaceManager(settings)
    reg = WorkflowRegistry(settings)
    engine = WorkflowEngine(wm)

    # 2. Retrieve Manifest
    manifest = reg.get_workflow("sample_workflow_multi_agent")

    # 3. Provide Runtime Inputs
    user_data = {"writing_topic": "Python uv guide", "content_length": 1000}

    # 4. Execute with Callbacks
    workflow_output = await engine.run(
        manifest,
        user_data,
        callbacks=[streamcallback_simple_print]
    )
```

- **WorkflowRegistry:** Handles discovery, schema validation, and logic checking.
- **WorkflowEngine:** Handles the step-by-step execution, template resolution, and blackboard updates.

---

## Developing New Workflow Step Types

Each task type requires three components defined in `myproject_core.workflow_tasks`:

1. **TaskParams:** A Pydantic model defining the task's allowed input parameters.
2. **TaskOutput:** A Pydantic model defining the data the task will write back to the blackboard.
3. **TaskClass:** A subclass of `BaseTask[TParams, TOutput]` implementing the `run()` logic.

```python
class PromptAgentTask(BaseTask[PromptAgentTaskParams, PromptAgentTaskOutput]):
    params_model = PromptAgentTaskParams
    output_model = PromptAgentTaskOutput

    async def run(self, context: JobContext, params: dict) -> PromptAgentTaskOutput:
        # Validate and coerce raw dictionary into typed params
        args = self.params_model.model_validate(params)

        # Execute business logic (e.g., LLM call)
        response_text = await agent.step(args.prompt)

        # Return typed output for the blackboard
        return self.output_model(content=response_text, file_path="...")
```

## Validation Layers

The workflow engine has three validation layers:

1. **Manifest Schema Validation:** Uses Pydantic models to verify YAML structure.
2. **Static Logic Validation (`_verify_logic`):** Before execution, renders all Jinja2 templates against a "mock blackboard" generated from task `output_model`s. Fails if a template references a non-existent field.
3. **Runtime Validation:** `WorkflowManifest.validate_runtime_inputs` ensures user-provided data matches types. Each task's `params_model` validates its input dict before execution.
