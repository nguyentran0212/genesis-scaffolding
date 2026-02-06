from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Set

import yaml
from pydantic import BaseModel, ConfigDict, Field


### LLM Configs
class LLMProvider(BaseModel):
    base_url: str
    api_key: str


class LLMModel(BaseModel):
    provider: LLMProvider
    model: str


### LLM Response Message
class LLMResponse(BaseModel):
    content: str
    reasoning_content: str


### Callback function for handling LLM response chunk
StreamCallback = Callable[[str], Awaitable[None]]


### Schema for workflow manifest yamls
class InputDefinition(BaseModel):
    """Defines a variable that the user must provide before the workflow starts."""

    type: str  # e.g., "string", "int", "file_list"
    description: str = Field(..., description="Help text for the user")
    default: Optional[Any] = None
    required: bool = False


class StepDefinition(BaseModel):
    """Defines a single executable unit within the workflow."""

    id: str = Field(..., description="Unique ID for this step to reference its data later")
    type: str = Field(..., description="The task type, e.g., 'prompt_agent' or 'file_ingest'")
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Configuration passed to the task. Can contain {{ placeholders }}.",
    )
    condition: Optional[str] = Field(
        None, description="A Jinja2 expression. If False, the step is skipped."
    )

    # We can add a method to validate the type later in the registry
    def validate_type(self, allowed_types: Set[str]):
        if self.type not in allowed_types:
            raise ValueError(
                f"Step '{self.id}' has unknown type '{self.type}'. Available types: {allowed_types}"
            )


class WorkflowManifest(BaseModel):
    """The root model for a .yaml workflow file."""

    model_config = ConfigDict(extra="forbid")  # Catches typos in top-level YAML keys

    name: str = Field(..., description="Human-readable name of the workflow")
    description: str = Field(..., description="What this workflow actually does")
    version: str = "1.0"

    # Map of input_name -> definition
    inputs: Dict[str, InputDefinition] = Field(default_factory=dict)

    # Ordered list of execution steps
    steps: List[StepDefinition]

    @classmethod
    def from_yaml(cls, path: Path) -> "WorkflowManifest":
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)
