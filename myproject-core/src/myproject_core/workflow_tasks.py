import ast
from os import write
import re
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Generic, Type, TypeVar

from myproject_tools.arxiv import get_paper_details
from myproject_tools.web_search import search_web
from pydantic import BaseModel, ConfigDict, field_validator

from myproject_core.agent_registry import AgentRegistry

from .workspace import JobContext


### BASE TASK CLASS
class TaskParams(BaseModel):
    """Common schema for all workflow task parameters."""

    model_config = ConfigDict(extra="ignore")

    files_to_read: list[Path] = []

    sub_directory: str | None = None
    write_response_to_file: bool = True
    write_response_to_output: bool = False
    output_filename: str = "response.txt"
    output_filename_prefix: str = "output_"

    @field_validator("files_to_read", mode="before")
    @classmethod
    def validate_to_path_list(cls, v: Any) -> list[Path]:
        if not v:
            return []

        # 1. Handle cases where 'v' is already a list (standard YAML list or Pydantic list)
        if isinstance(v, list):
            return cls._resolve_items_to_paths(v)

        # 2. Handle string inputs (Jinja resolutions or single string params)
        if isinstance(v, str):
            v = v.strip()

            # 2a. Remove "PosixPath(...)" or "WindowsPath(...)" wrappers from the string
            # This turns "[PosixPath('/path')]" into "['/path']"
            v = re.sub(r"(?:PosixPath|WindowsPath|Path)\(['\"](.+?)['\"]\)", r"'\1'", v)

            # 2b. If it's a stringified list "[...]"
            if v.startswith("[") and v.endswith("]"):
                try:
                    parsed = ast.literal_eval(v)
                    if isinstance(parsed, list):
                        return cls._resolve_items_to_paths(parsed)
                    return [Path(str(parsed))]
                except (ValueError, SyntaxError):
                    # Manual fallback for comma-separated strings inside brackets
                    items = v.strip("[]").split(",")
                    return [Path(i.strip().strip("'\"")) for i in items if i.strip()]

            # 2c. Single string path
            return [Path(v)]

        return []

    @staticmethod
    def _resolve_items_to_paths(items: list) -> list[Path]:
        """Helper to ensure every item in a list is a Path object."""
        result = []
        for item in items:
            if not item:
                continue
            # If the item itself is a stringified list (nested accidentally)
            if isinstance(item, str) and item.startswith("["):
                # Recursive call to handle nested list strings
                result.extend(TaskParams._resolve_items_to_paths([item.strip("[]")]))
            else:
                result.append(Path(str(item).strip("'\" ")))
        return result


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

    def resolve_input_file_paths(self, input_file_paths: list[Path], context: JobContext) -> list[Path]:
        """
        Resolve and dedup the input file paths provided to the workflow task
        """
        resolved_files: list[Path] = []
        for path_str in input_file_paths:
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
                # Recursively find all files in the directory
                for item in base_path.rglob("*"):
                    if item.is_file():
                        resolved_files.append(item.absolute())
            else:
                resolved_files.append(base_path.absolute())

        unique_files = list(set(resolved_files))
        return unique_files

    def write_content_to_files(
        self,
        content: list[str],
        context: JobContext,
        output_filename: str,
        output_filename_prefix: str,
        write_response_to_output: bool,
        extension: str = "md",
        sub_directory: str | None = None,
    ) -> list[Path]:
        def _get_file_name(
            content: list[str],
            index: int,
            output_filename: str,
            output_filename_prefix: str,
            extension: str,
        ):
            if len(content) == 1:
                return output_filename
            else:
                return f"{output_filename_prefix}_{index}.{extension}"

        # Determine target directories
        target_dirs: list[Path] = []

        sub_dir = sub_directory or ""

        internal_dir = context.internal / sub_dir
        internal_dir.mkdir(parents=True, exist_ok=True)
        target_dirs.append(internal_dir)

        if write_response_to_output:
            output_dir = context.output / sub_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            target_dirs.append(output_dir)

        # Write content items to files
        all_written_paths: list[Path] = []
        for i, content_item in enumerate(content):
            filename = _get_file_name(
                content=content,
                index=i,
                output_filename=output_filename,
                output_filename_prefix=output_filename_prefix,
                extension=extension,
            )

            for target_dir in target_dirs:
                target_file = target_dir / filename
                target_file.write_text(content_item, encoding="utf-8")

                all_written_paths.append(target_file)

        return all_written_paths


### SAMPLE TASK
class SampleTaskParams(TaskParams):
    pass


class SampleTaskOutput(TaskOutput):
    pass


class SampleTask(BaseTask[SampleTaskParams, SampleTaskOutput]):
    params_model = SampleTaskParams
    output_model = SampleTaskOutput

    async def run(self, context: JobContext, agent_registry: AgentRegistry, params: dict) -> output_model:
        args = self.params_model.model_validate(params)
        output = self.output_model(content=[""], file_paths=None)
        return output


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


# Prompting an LLM agent
class PromptAgentTaskParams(TaskParams):
    agent: str
    prompt: str


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

        # Resolve the list of files to read
        unique_files = self.resolve_input_file_paths(context=context, input_file_paths=args.files_to_read)

        # Add the files to the clipboard of the agent
        for file_path in unique_files:
            await agent.add_file(file_path)

        # Trigger the agent to get a response text
        response_text = await agent.step(args.prompt)

        # Write to file if required
        if args.write_response_to_file:
            output_paths = self.write_content_to_files(
                content=[str(response_text)],
                context=context,
                output_filename=args.output_filename,
                output_filename_prefix=args.output_filename_prefix,
                write_response_to_output=args.write_response_to_output,
            )
            return self.output_model(content=[str(response_text)], file_paths=output_paths)
        else:
            return self.output_model(content=[str(response_text)])


### Arxiv paper download tasks
class ArxivDownloadTaskParams(TaskParams):
    arxiv_paper_id: str


class ArxivDownloadTaskOutput(TaskOutput):
    pass


class ArxivDownloadTask(BaseTask[ArxivDownloadTaskParams, ArxivDownloadTaskOutput]):
    params_model = ArxivDownloadTaskParams
    output_model = ArxivDownloadTaskOutput

    async def run(self, context: JobContext, agent_registry: AgentRegistry, params: dict) -> output_model:
        args = self.params_model.model_validate(params)
        arxiv_paper_id = args.arxiv_paper_id
        sub_directory = args.sub_directory

        if not sub_directory:
            sub_directory = ""
        download_directory = context.internal / sub_directory
        paper_details = get_paper_details(
            paper_id=arxiv_paper_id, download_dir=download_directory, download_pdf=True
        )
        if not paper_details:
            raise ValueError(f"Cannot find the given arxiv paper id: {arxiv_paper_id}")
        pdf_path = paper_details["pdf_path"]
        md_path = paper_details["md_path"]

        output = self.output_model(content=[f"{paper_details}"], file_paths=[pdf_path, md_path])
        return output


### SAMPLE TASK
class WebSearchTaskParams(TaskParams):
    query: str
    number_of_results: int = 10
    output_filename_prefix: str = "search_results"


class WebSearchTaskOutput(TaskOutput):
    pass


class WebSearchTask(BaseTask[WebSearchTaskParams, WebSearchTaskOutput]):
    params_model = WebSearchTaskParams
    output_model = WebSearchTaskOutput

    async def run(self, context: JobContext, agent_registry: AgentRegistry, params: dict) -> output_model:
        args = self.params_model.model_validate(params)

        web_search_results = await search_web(
            query=args.query, max_results=args.number_of_results, fetch_full=True
        )
        if not web_search_results:
            raise ValueError(f"Cannot find any search result for the query {args.query}")

        # 2. Process results into Markdown strings
        formatted_contents = []
        for i, res in enumerate(web_search_results, start=1):
            # Extract content from the Pydantic FetchResult, fallback to snippet if fetch failed
            main_body = res.snippet
            if res and res.full_content:
                main_body = res.full_content

            # Create a structured Markdown block for this specific result
            md_entry = f"# {res.title}\n**URL:** {res.url}\n\n{main_body}\n\n---\n"
            formatted_contents.append(md_entry)

        all_written_paths = self.write_content_to_files(
            content=formatted_contents,
            context=context,
            output_filename=args.output_filename,
            output_filename_prefix=args.output_filename_prefix,
            write_response_to_output=args.write_response_to_output,
        )

        # 4. Return the structured output
        return self.output_model(
            content=formatted_contents, file_paths=all_written_paths if all_written_paths else None
        )


# This dictionary is what the Registry will use to verify YAMLs
TASK_LIBRARY = {
    "file_ingest": IngestTask,
    "prompt_agent": PromptAgentTask,
    "arxiv_download": ArxivDownloadTask,
    "web_search": WebSearchTask,
}
