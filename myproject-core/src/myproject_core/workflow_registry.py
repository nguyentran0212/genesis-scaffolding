from pathlib import Path

from .schemas import WorkflowManifest
from .workflow_tasks import TASK_LIBRARY


class WorkflowRegistry:
    def __init__(self, workflow_dir: Path):
        self.workflow_dir = workflow_dir
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
                self._verify_steps(manifest)

                # 3. Register using the filename (stem) as the ID
                self.workflows[yaml_file.stem] = manifest

            except Exception as e:
                print(f"Error loading workflow '{yaml_file.name}': {e}")

    def _verify_steps(self, manifest: WorkflowManifest):
        allowed = set(TASK_LIBRARY.keys())
        for step in manifest.steps:
            step.validate_type(allowed)

    def get_workflow(self, name: str) -> WorkflowManifest | None:
        return self.workflows.get(name)
