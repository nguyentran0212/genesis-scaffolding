import jinja2

from .configs import Config
from .schemas import WorkflowManifest
from .utils import resolve_placeholders
from .workflow_tasks import TASK_LIBRARY


class WorkflowRegistry:
    def __init__(self, settings: Config):
        self.workflow_dir = settings.path.workflow_directory
        self.workflows: dict[str, WorkflowManifest] = {}
        self.load_all()

    def load_all(self):
        """Scans the directory and populates the registry."""
        if not self.workflow_dir.exists():
            return

        for yaml_file in self.workflow_dir.glob("*.yaml"):
            try:
                # 1. Basic Pydantic validation
                manifest = WorkflowManifest.from_yaml(yaml_file)

                # 2. Step Type validation
                self._verify_logic(manifest)

                # 3. Register using the filename (stem) as the ID
                self.workflows[yaml_file.stem] = manifest

            except Exception as e:
                print(f"Error loading workflow '{yaml_file.name}': {e}")

    def _verify_logic(self, manifest: WorkflowManifest):
        """Dry-run Jinja2 templates using dummy data from Task models."""
        # 1. Mock the Blackboard
        fake_state = {"inputs": {k: v.default for k, v in manifest.inputs.items()}, "steps": {}}

        # 2. Populate 'steps' with dummy data based on output_models
        for step in manifest.steps:
            task_cls = TASK_LIBRARY.get(step.type)
            if not task_cls:
                raise ValueError(f"Task type '{step.type}' not found.")

            # Use model_json_schema to get keys, or model_construct for a dummy obj
            output_keys = task_cls.output_model.model_fields.keys()
            dummy_output = {key: "dummy_val" for key in output_keys}

            fake_state["steps"][step.id] = dummy_output

        # Validate Step Params and Workflow Outputs
        try:
            for step in manifest.steps:
                resolve_placeholders(step.params, fake_state)

            # Check Workflow Outputs
            raw_outputs = {k: v.value for k, v in manifest.outputs.items()}
            resolve_placeholders(raw_outputs, fake_state)
        except jinja2.exceptions.UndefinedError as e:
            raise ValueError(f"Logic error: {e}")

    def get_workflow(self, name: str) -> WorkflowManifest | None:
        return self.workflows.get(name)
