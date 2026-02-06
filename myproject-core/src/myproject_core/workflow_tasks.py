from abc import ABC, abstractmethod

from pydantic import BaseModel, ConfigDict

from .workspace import JobContext


class BaseTask(ABC):
    class Params(BaseModel):
        """
        Params class defines the schema of the parameters that a step accept.
        This is used for validating the task's inputs defined in a workflow manifest yaml
        """

        model_config = ConfigDict(extra="ignore")

    @abstractmethod
    def run(self, context: JobContext, params: dict):
        pass


class IngestTask(BaseTask):
    def run(self, context: JobContext, params: dict):
        print(f"Ingesting files using method: {params.get('method')}")


class AgentTask(BaseTask):
    def run(self, context: JobContext, params: dict):
        print(f"Calling LLM with prompt: {params.get('prompt')}")


# This dictionary is what the Registry will use to verify YAMLs
TASK_LIBRARY = {
    "file_ingest": IngestTask,
    "prompt_agent": AgentTask,
}
