from myproject_tools.web_search import search_web

from ..agent_registry import AgentRegistry
from ..schemas import JobContext
from .base_task import BaseTask, TaskOutput, TaskParams


class WebSearchTaskParams(TaskParams):
    query: list[str]
    number_of_results: int = 10
    output_filename_prefix: str = "search_results"


class WebSearchTaskOutput(TaskOutput):
    pass


class WebSearchTask(BaseTask[WebSearchTaskParams, WebSearchTaskOutput]):
    params_model = WebSearchTaskParams
    output_model = WebSearchTaskOutput

    async def run(self, context: JobContext, agent_registry: AgentRegistry, params: dict) -> output_model:
        args = self.params_model.model_validate(params)

        query_string = " ".join(args.query)
        print(args.query)
        print(query_string)

        web_search_results = await search_web(
            query=query_string, max_results=args.number_of_results, fetch_full=True
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

        all_written_paths = await self.write_content_to_files(
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
