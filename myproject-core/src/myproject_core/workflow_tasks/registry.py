from .arxiv_download import ArxivDownloadTask
from .arxiv_search import ArxivSearchTask
from .file_ingest import IngestTask
from .list_extractor import ListExtractorTask
from .prompt_agent import PromptAgentTask
from .web_fetch import WebFetchTask
from .web_search import WebSearchTask

TASK_LIBRARY = {
    "file_ingest": IngestTask,
    "prompt_agent": PromptAgentTask,
    "arxiv_download": ArxivDownloadTask,
    "web_search": WebSearchTask,
    "arxiv_search": ArxivSearchTask,
    "list_extractor": ListExtractorTask,
    "web_fetch": WebFetchTask,
}
