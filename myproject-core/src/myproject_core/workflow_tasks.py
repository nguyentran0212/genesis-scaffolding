from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar

from pydantic import BaseModel, ConfigDict

from .agent import Agent
from .configs import settings
from .schemas import AgentConfig, LLMModel, LLMProvider
from .workspace import JobContext


class TaskParams(BaseModel):
    """Common schema for all workflow task parameters."""

    model_config = ConfigDict(extra="ignore")


class TaskOutput(BaseModel):
    """Common schema for all workflow task output."""

    model_config = ConfigDict(extra="ignore")


TParams = TypeVar("TParams", bound=TaskParams)
TOutput = TypeVar("TOutput", bound=TaskOutput)


class BaseTask(ABC, Generic[TParams, TOutput]):
    params_model: Type[TParams]
    output_model: Type[TOutput]

    @abstractmethod
    async def run(self, context: JobContext, params: dict) -> TOutput:
        pass


class IngestTask(BaseTask):
    async def run(self, context: JobContext, params: dict):
        print(f"Ingesting files using method: {params.get('method')}")


class PromptAgentTaskParams(TaskParams):
    prompt: str
    output_filename: str = "response.txt"


class PromptAgentTaskOutput(TaskOutput):
    content: str
    file_path: str | None = None


class PromptAgentTask(BaseTask[PromptAgentTaskParams, PromptAgentTaskOutput]):
    params_model = PromptAgentTaskParams
    output_model = PromptAgentTaskOutput

    async def run(self, context: JobContext, params: dict) -> PromptAgentTaskOutput:
        # args = self.params_model(**params)
        args = self.params_model.model_validate(params)

        # 1. Initialize Agent (Using your provided snippet logic)
        provider = LLMProvider(base_url=settings.llm.base_url, api_key=settings.llm.api_key)
        model = LLMModel(provider=provider, model=settings.llm.model)
        agent_config = AgentConfig(name="my-agent", llm_config=model)
        agent = Agent(agent_config)

        # 2. Execute
        response_text = await agent.step(args.prompt)

        # 3. Write to Output Directory
        output_path = context.output / args.output_filename
        output_path.write_text(str(response_text))

        return self.output_model(content=str(response_text), file_path=str(output_path))


# This dictionary is what the Registry will use to verify YAMLs
TASK_LIBRARY = {
    "file_ingest": IngestTask,
    "prompt_agent": PromptAgentTask,
}
