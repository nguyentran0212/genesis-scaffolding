import shutil
from pathlib import Path

from ..agent_registry import AgentRegistry
from ..schemas import JobContext
from .base_task import BaseTask, TaskOutput, TaskParams


class IngestTaskParams(TaskParams):
    pass


class IngestTaskOutput(TaskOutput):
    pass


class IngestTask(BaseTask[IngestTaskParams, IngestTaskOutput]):
    params_model = IngestTaskParams
    output_model = IngestTaskOutput

    async def run(
        self, context: JobContext, agent_registry: AgentRegistry, params: dict
    ) -> IngestTaskOutput:
        args = self.params_model.model_validate(params)

        # Determine and create the target directory
        target_dir = context.input
        if args.sub_directory:
            target_dir = context.input / args.sub_directory

        target_dir.mkdir(parents=True, exist_ok=True)

        # Expand directory to file list
        # Resolve to a complete list of files to read
        files_to_process = self.resolve_input_file_paths(
            context=context, input_file_paths=args.files_to_read
        )

        # Process the resolved file list
        successful_ingests: list[Path] = []
        for source_path in files_to_process:
            dest_path = target_dir / source_path.name

            try:
                # Clean up existing link/file if it exists
                if dest_path.exists() or dest_path.is_symlink():
                    dest_path.unlink()

                # Attempt Symlink
                try:
                    dest_path.symlink_to(source_path)
                except (OSError, PermissionError):
                    # Fallback to Copy
                    shutil.copy2(source_path, dest_path)

                # If no exception occurred, record the destination path
                successful_ingests.append(dest_path)

            except Exception as e:
                # Log or handle specific file failures here if needed
                # For now, we'll re-raise to keep the "throw on error" behavior
                raise e

        return self.output_model(
            content=[f"Ingested these files: {successful_ingests}"], file_paths=successful_ingests
        )
