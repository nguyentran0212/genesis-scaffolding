from typing import Any, Dict, cast

import jinja2

from .schemas import WorkflowManifest
from .workflow_tasks import TASK_LIBRARY
from .workspace import JobContext, WorkspaceManager


class WorkflowEngine:
    def __init__(self, workspace_manager: WorkspaceManager):
        self.workspace = workspace_manager
        # Setup Jinja2 environment for parameter interpolation
        self.jinja_env = jinja2.Environment(
            undefined=jinja2.StrictUndefined  # Errors out if a variable is missing
        )

    def run(self, manifest: WorkflowManifest, user_inputs: Dict[str, Any]) -> JobContext:
        """Executes a validated workflow manifest."""

        # 1. Initialize Workspace/Job
        job_context = self.workspace.create_job(manifest.name)

        # 2. Initialize the "Blackboard" State
        state = {"inputs": user_inputs, "steps": {}}

        # 3. Iterate through steps
        for step_def in manifest.steps:
            # Check condition if present
            if step_def.condition and not self._evaluate_condition(step_def.condition, state):
                continue

            # A. Resolve placeholders in params using current state
            resolved_params = self._resolve_placeholders(step_def.params, state)

            # B. Get the Task class from the library
            task_class = TASK_LIBRARY[step_def.type]
            task_instance = task_class()

            # C. Execute Task
            # We pass the job_context for file access and the resolved params for logic
            output = task_instance.run(job_context, resolved_params)

            # D. Update State
            state["steps"][step_def.id] = output

            # E. Checkpoint: Optional - save state to internal/state.json
            self._checkpoint(job_context, state)

        return job_context

    def _resolve_placeholders(self, params: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively renders Jinja2 strings in the params dictionary."""

        def render_value(val):
            if isinstance(val, str) and "{{" in val:
                template = self.jinja_env.from_string(val)
                return template.render(**state)
            if isinstance(val, dict):
                return {k: render_value(v) for k, v in val.items()}
            if isinstance(val, list):
                return [render_value(i) for i in val]
            return val

        return cast(Dict[str, Any], render_value(params))

    def _evaluate_condition(self, condition: str, state: Dict[str, Any]) -> bool:
        """Evaluates a boolean string like 'inputs.depth > 3'"""
        template = self.jinja_env.from_string(f"{{{{ {condition} }}}}")
        result = template.render(**state)
        return result.lower() == "true"

    def _checkpoint(self, context: JobContext, state: Dict[str, Any]):
        """Persists the current state to the job directory for debugging/resume."""
        import json

        state_path = context.internal / "workflow_state.json"
        with open(state_path, "w") as f:
            # Note: You'll need a way to serialize complex objects if tasks return them
            json.dump(state, f, indent=2, default=str)
