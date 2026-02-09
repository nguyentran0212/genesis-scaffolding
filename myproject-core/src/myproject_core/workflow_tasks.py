from abc import ABC, abstractmethod
from typing import Generic, Type, TypeVar

from myproject_core.agent_registry import AgentRegistry
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
    async def run(self, context: JobContext, agent_registry: AgentRegistry, params: dict) -> TOutput:
        pass


class IngestTask(BaseTask):
    async def run(self, context: JobContext, agent_registry: AgentRegistry, params: dict):
        print(f"Ingesting files using method: {params.get('method')}")


class PromptAgentTaskParams(TaskParams):
    agent: str
    prompt: str
    write_file: bool = True
    write_to_output: bool = True
    output_filename: str = "response.txt"


class PromptAgentTaskOutput(TaskOutput):
    content: str
    file_path: str | None = None


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

        # Trigger the agent to get a response text
        response_text = await agent.step(args.prompt)

        # Write to Directory if required
        if args.write_file:
            # Always write to internal
            output_paths = [context.internal / args.output_filename]
            if args.write_to_output:
                # If requested to write to output, will also write to output
                output_paths.append(context.output / args.output_filename)

            for output_path in output_paths:
                output_path.write_text(str(response_text))
            # Return path in output directory if available, otherwise return the internal path
            return self.output_model(content=str(response_text), file_path=str(output_paths[-1]))
        else:
            return self.output_model(content=str(response_text))


# This dictionary is what the Registry will use to verify YAMLs
TASK_LIBRARY = {
    "file_ingest": IngestTask,
    "prompt_agent": PromptAgentTask,
}
