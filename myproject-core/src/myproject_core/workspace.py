import re
import unicodedata
from datetime import datetime
from pathlib import Path

from .configs import Config, settings


class JobContext:
    """
    A value object representing an active job session.
    This is what the agent or workflow logic interacts with.
    """

    def __init__(self, root: Path):
        self.root = root
        self.input = root / "input"
        self.internal = root / "internal"
        self.output = root / "output"

    def __repr__(self) -> str:
        return f"<JobContext {self.root.name}>"


class WorkspaceManager:
    def __init__(self, settings: Config):
        self.settings = settings
        # Ensure the base 'workspaces' folder exists immediately
        self.settings.path.workspace_directory.mkdir(parents=True, exist_ok=True)

    def _slugify(self, text: str) -> str:
        """
        Transforms user input into a filesystem-safe string.
        'My Project!!' -> 'my-project'
        """
        # Normalize unicode (removes accents)
        text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
        # Remove non-word characters and replace spaces/underscores with hyphens
        text = re.sub(r"[^\w\s-]", "", text).lower()
        text = re.sub(r"[-\s]+", "-", text).strip("-")
        # Limit length to keep paths manageable
        return text[:64] or "untitled-job"

    def _generate_unique_path(self, name: str) -> Path:
        """
        Combines slug, timestamp, and collision checks.
        """
        slug = self._slugify(name)

        # Handle Windows reserved names
        reserved = {"con", "prn", "aux", "nul", "com1", "com2", "lpt1"}
        if slug in reserved:
            slug = f"safe-{slug}"

        # Create a timestamped folder name (Sortable and unique)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dir_name = f"{timestamp}_{slug}"

        return self.settings.path.workspace_directory / dir_name

    def create_job(self, name: str) -> JobContext:
        """
        The main entry point: creates the physical directory structure
        and returns the JobContext.
        """
        job_path = self._generate_unique_path(name)

        # Create the 'Russian Doll' structure
        job_path.mkdir(parents=True, exist_ok=False)
        (job_path / "input").mkdir()
        (job_path / "internal").mkdir()
        (job_path / "output").mkdir()

        # Optional: Save original name to internal metadata for UI display
        with open(job_path / "internal" / "meta.txt", "w") as f:
            f.write(f"Original Name: {name}\nCreated: {datetime.now().isoformat()}")

        return JobContext(job_path)

    def validate_path_safety(self, job: JobContext, target_path: Path) -> bool:
        """
        Security check: Ensures a file operation is within the job root.
        Use this before any agent-driven 'write' or 'read' operation.
        """
        try:
            # Resolve to absolute paths to handle '..' tricks
            abs_job_root = job.root.resolve()
            abs_target = target_path.resolve()
            return abs_target.is_relative_to(abs_job_root)
        except (ValueError, OSError):
            return False


def main():
    print(settings.path)
    workspace_manager = WorkspaceManager(settings)
    job_context = workspace_manager.create_job("my testing workspace dir")
    print(job_context)


if __name__ == "__main__":
    main()
