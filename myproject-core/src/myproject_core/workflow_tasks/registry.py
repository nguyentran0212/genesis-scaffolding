from .arxiv_download import ArxivDownloadTask
from .arxiv_search import ArxivSearchTask
from .file_ingest import IngestTask
from .prompt_agent import PromptAgentTask
from .web_search import WebSearchTask

TASK_LIBRARY = {
    "file_ingest": IngestTask,
    "prompt_agent": PromptAgentTask,
    "arxiv_download": ArxivDownloadTask,
    "web_search": WebSearchTask,
    "arxiv_search": ArxivSearchTask,
}
