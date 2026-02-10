import ast
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Generic, Type, TypeVar, Union

from pydantic import BaseModel, ConfigDict, field_validator

from myproject_core.agent_registry import AgentRegistry

from .workspace import JobContext


### BASE TASK CLASS
class TaskParams(BaseModel):
    """Common schema for all workflow task parameters."""

    model_config = ConfigDict(extra="ignore")

    files_to_read: list[Path] = []

    sub_directory: str | None = None

    @field_validator("files_to_read", mode="before")
    @classmethod
    def handle_string_list(cls, v: Union[str, list[str]]) -> list[str]:
        # If the input is a string that starts with '[', try to parse it
        if isinstance(v, str) and v.startswith("[") and v.endswith("]"):
            try:
                # Safely convert string representation of list to actual list
                return ast.literal_eval(v)
            except (ValueError, SyntaxError):
                return [v]  # Fallback to single-item list

        # If it's just a single string (not a list), wrap it in a list
        if isinstance(v, str):
            return [v]

        return v


class TaskOutput(BaseModel):
    """Common schema for all workflow task output."""

    model_config = ConfigDict(extra="ignore")
    content: list[str]
    file_paths: list[Path] | None = None


TParams = TypeVar("TParams", bound=TaskParams)
TOutput = TypeVar("TOutput", bound=TaskOutput)


class BaseTask(ABC, Generic[TParams, TOutput]):
    params_model: Type[TParams]
    output_model: Type[TOutput]

    @abstractmethod
    async def run(self, context: JobContext, agent_registry: AgentRegistry, params: dict) -> TOutput:
        pass


### CONCRETE TASK CLASSES
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

        # 1. Determine and create the target directory
        target_dir = context.input
        if args.sub_directory:
            target_dir = context.input / args.sub_directory

        target_dir.mkdir(parents=True, exist_ok=True)

        # 2. Expand directories into a flat list of files
        files_to_process = set()
        for path_str in args.files_to_read:
            path = Path(path_str)

            if not path.exists():
                raise FileNotFoundError(f"Path does not exist: {path_str}")

            if path.is_dir():
                # Recursively find all files in the directory
                for item in path.rglob("*"):
                    if item.is_file():
                        files_to_process.add(item.absolute())
            else:
                files_to_process.add(path.absolute())

        # 3. Process the resolved file list
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


# Prompting an LLM agent
class PromptAgentTaskParams(TaskParams):
    agent: str
    prompt: str
    write_response_to_file: bool = True
    write_response_to_output: bool = False
    output_filename: str = "response.txt"


class PromptAgentTaskOutput(TaskOutput):
    pass


class PromptAgentTask(BaseTask[PromptAgentTaskParams, PromptAgentTaskOutput]):
    params_model = PromptAgentTaskParams
    output_model = PromptAgentTaskOutput

    async def run(
        self, context: JobContext, agent_registry: AgentRegistry, params: dict
    ) -> PromptAgentTaskOutput:
        # args = self.params_model(**params)
        args = self.params_model.model_validate(params)

        # Initialize agent by querying agent registry
        agent = agent_registry.get_agent(args.agent)
        if not agent:
            raise Exception(f"Cannot find the requested agent {args.agent}")

        # Add files to the agent's clipboard
        resolved_files: list[Path] = []
        for path_str in args.files_to_read:
            raw_path = Path(path_str)

            # If absolute, use as is; if relative, join with context.root
            if raw_path.is_absolute():
                base_path = raw_path
            else:
                base_path = (context.root / raw_path).resolve()

            if not base_path.exists():
                # You can choose to throw or log; following your previous pattern:
                raise FileNotFoundError(f"Resolved path does not exist: {base_path}")

            # 2. Directory vs File Handling
            if base_path.is_dir():
                # Collect all files within the directory (non-recursive example)
                # Use .rglob("*") if you want deep nesting
                for item in base_path.iterdir():
                    if item.is_file():
                        resolved_files.append(item.absolute())
            else:
                resolved_files.append(base_path.absolute())

        # Add files to Agent Clipboard
        # Deduplicate to avoid redundant processing
        unique_files = list(set(resolved_files))

        for file_path in unique_files:
            await agent.add_file(file_path)

        # Trigger the agent to get a response text
        response_text = await agent.step(args.prompt)

        # Write to Directory if required
        if args.write_response_to_file:
            # Always write to internal
            if not args.sub_directory:
                args.sub_directory = ""  # This simplifies the output paths appending below
            output_paths = [context.internal / args.sub_directory / args.output_filename]
            if args.write_response_to_output:
                # If requested to write to output, will also write to output
                output_paths.append(context.output / args.output_filename)

            for output_path in output_paths:
                output_path.write_text(str(response_text))
            # Return path in output directory if available, otherwise return the internal path
            return self.output_model(content=[str(response_text)], file_paths=output_paths)
        else:
            return self.output_model(content=[str(response_text)])


# This dictionary is what the Registry will use to verify YAMLs
TASK_LIBRARY = {
    "file_ingest": IngestTask,
    "prompt_agent": PromptAgentTask,
}
