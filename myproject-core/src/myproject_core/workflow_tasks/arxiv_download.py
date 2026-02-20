import asyncio
from pathlib import Path

from myproject_tools.arxiv import get_paper_details

from ..agent_registry import AgentRegistry
from ..schemas import JobContext
from .base_task import BaseTask, TaskOutput, TaskParams


### Arxiv paper download tasks
class ArxivDownloadTaskParams(TaskParams):
    # Accept a list of paper IDs
    arxiv_paper_ids: list[str]
    write_response_to_output: bool = True
    output_filename_prefix: str = "arxiv_"


class ArxivDownloadTaskOutput(TaskOutput):
    # Return lists of Path objects
    pdf_paths: list[Path]
    md_paths: list[Path]


class ArxivDownloadTask(BaseTask[ArxivDownloadTaskParams, ArxivDownloadTaskOutput]):
    params_model = ArxivDownloadTaskParams
    output_model = ArxivDownloadTaskOutput

    async def run(self, context: JobContext, agent_registry: AgentRegistry, params: dict) -> output_model:
        args = self.params_model.model_validate(params)

        print(args)
        arxiv_paper_ids = args.arxiv_paper_ids
        sub_directory = args.sub_directory or ""
        download_directory = context.internal / sub_directory

        # Ensure download directory exists
        download_directory.mkdir(parents=True, exist_ok=True)

        pdf_paths: list[Path] = []
        md_paths: list[Path] = []
        all_details = []

        # Sequential processing to avoid arXiv IP blocking
        for paper_id in arxiv_paper_ids:
            # Inner function to handle the blocking IO for a single paper
            def _do_blocking_download(pid: str):
                details = get_paper_details(
                    paper_id=pid, download_dir=download_directory, download_pdf=True
                )
                if not details:
                    raise ValueError(f"Cannot find the given arxiv paper id: {pid}")
                return details

            # Execute the single download in a thread and wait for it to finish
            paper_details = await asyncio.to_thread(_do_blocking_download, paper_id)

            # Convert string paths to Path objects and append to our lists
            # This ensures the index across both lists matches
            pdf_paths.append(Path(paper_details["pdf_path"]))
            md_paths.append(Path(paper_details["md_path"]))
            all_details.append(paper_details)

        if args.write_response_to_output:
            await self.link_or_copy_to_output(
                context=context,
                internal_file_paths=pdf_paths,
                output_filename=args.output_filename,
                output_filename_prefix=args.output_filename_prefix,
                sub_directory=args.sub_directory,
            )

        # Return the lists of Paths
        return self.output_model(
            content=[str(d) for d in all_details],
            # Combining both for the base class file_paths requirement (as strings)
            file_paths=md_paths,
            # Specific fields for the two matching Path lists
            pdf_paths=pdf_paths,
            md_paths=md_paths,
        )
