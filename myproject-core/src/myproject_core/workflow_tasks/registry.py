from .agent_map import AgentMapTask
from .agent_projection import AgentProjectionTask
from .arxiv_download import ArxivDownloadTask
from .arxiv_search import ArxivSearchTask
from .file_ingest import IngestTask
from .web_fetch import WebFetchTask
from .web_search import WebSearchTask

TASK_LIBRARY = {
    "file_ingest": IngestTask,
    "agent_map": AgentMapTask,
    "arxiv_download": ArxivDownloadTask,
    "web_search": WebSearchTask,
    "arxiv_search": ArxivSearchTask,
    "agent_projection": AgentProjectionTask,
    "web_fetch": WebFetchTask,
}
