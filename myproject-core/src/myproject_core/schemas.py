from enum import Enum
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


### JobContext object to be used by workspace manager
class JobContext:
    """
    A value object representing an active job session of a workflow
    This is what the agent or workflow logic interacts with.
    """

    def __init__(self, root: Path):
        self.root = root
        self.input = root / "input"
        self.internal = root / "internal"
        self.output = root / "output"

    def __repr__(self) -> str:
        return f"<JobContext {self.root.name}>"


### LLM Configs
class LLMProvider(BaseModel):
    base_url: str
    api_key: str


class LLMModel(BaseModel):
    """
    TODO: support other inference parameters such as temperature and repeat penalty
    """

    provider: LLMProvider
    model: str


### LLM Response Message
class LLMResponse(BaseModel):
    content: str
    reasoning_content: str


### Callback function for handling LLM response chunk
StreamCallback = Callable[[str], Awaitable[None]]


### Agent Configs
class AgentConfig(BaseModel):
    # Name of the agent for referring to it in the system
    name: str
    # LLM Configuration to be used by this model
    llm_config: LLMModel | None = None
    # Only interactive agent can be used in chat
    interactive: bool = False
    # System prompt for the agent
    system_prompt: str = "You are a helpful AI agent."
    # List of allowed tools
    allowed_tools: list[Any] = []
    # List of names of allowed agents for delegation
    allowed_agents: list[str] = []


### Agent's clipboard content
class AgentClipboardFile(BaseModel):
    # Path to the file
    file_path: Path
    # Content of the file (support textual content only for now)
    file_content: str


class AgentClipboardTodoItem(BaseModel):
    # Completion status of the task
    completed: bool = False
    # Textual description of the task
    task_desc: str


class AgentClipboard(BaseModel):
    accessed_files: list[AgentClipboardFile] = []
    todo_list: list[AgentClipboardTodoItem] = []

    def render_to_markdown(self) -> str:
        """Converts clipboard contents into a structured Markdown string."""
        sections = []

        # Render Todo List
        if self.todo_list:
            todo_section = "### TODO LIST\n"
            for item in self.todo_list:
                status = "[x]" if item.completed else "[ ]"
                todo_section += f"{status} {item.task_desc}\n"
            sections.append(todo_section)

        # Render Files
        if self.accessed_files:
            file_section = "### ACCESSED FILES\n"
            for file in self.accessed_files:
                file_section += f"#### File: {file.file_path}\n"
                file_section += f"```\n{file.file_content}\n```\n"
            sections.append(file_section)

        if not sections:
            return "Clipboard is currently empty."

        return "\n\n".join(sections)


### Schema for workflow events to use with callbacks to communicate events happening during workflow runs
class WorkflowEventType(str, Enum):
    STEP_START = "step_start"
    STEP_COMPLETED = "step_completed"
    LOG = "log"
    ERROR = "error"


class WorkflowEvent(BaseModel):
    event_type: WorkflowEventType
    step_id: Optional[str] = None
    message: str
    data: Any | None = None  # Holds the output object or specific metadata


WorkflowCallback = Callable[[WorkflowEvent], Awaitable[None]]


### Schema for workflow manifest yamls
class WorkflowInputType(str, Enum):
    """
    Data types of workflow inputs for the workflow manifests
    """

    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    FILE = "file"
    DIR = "dir"
    LIST_STRING = "list[string]"
    LIST_FILE = "list[file]"


# Map our WorkflowInputType Enum to actual Python types for Pydantic to do run-time validation
TYPE_MAP: Dict[WorkflowInputType, Any] = {
    WorkflowInputType.STRING: str,
    WorkflowInputType.INT: int,
    WorkflowInputType.FLOAT: float,
    WorkflowInputType.BOOL: bool,
    WorkflowInputType.FILE: Path,
    WorkflowInputType.DIR: Path,
    WorkflowInputType.LIST_STRING: List[str],
    WorkflowInputType.LIST_FILE: List[Path],
}


class InputDefinition(BaseModel):
    """Defines a variable that the user must provide before the workflow starts."""

    type: WorkflowInputType
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


class OutputDefinition(BaseModel):
    """Defines an output from the workflow."""

    description: str = Field(..., description="Help text for the user")
    value: str = Field(
        ..., description="Contain {{ placeholders }} that specifies data source for this output."
    )


class WorkflowManifest(BaseModel):
    """The root model for a .yaml workflow file."""

    model_config = ConfigDict(extra="forbid")  # Catches typos in top-level YAML keys

    name: str = Field(..., description="Human-readable name of the workflow")
    description: str = Field(..., description="What this workflow actually does")
    version: str = "1.0"

    # Map of input_name -> definition
    inputs: dict[str, InputDefinition] = Field(default_factory=dict)

    # Ordered list of execution steps
    steps: list[StepDefinition]

    # Map of output_name -> definition
    outputs: dict[str, OutputDefinition]

    def validate_runtime_inputs(self, raw_data: dict) -> dict:
        """
        Validate the raw input data to a workflow against its type definition stored in input dict
        """
        validated = {}
        for name, defn in self.inputs.items():
            raw_val = raw_data.get(name, defn.default)

            # Handle Required / None
            if raw_val is None:
                if defn.required:
                    raise ValueError(f"Input '{name}' is required.")
                validated[name] = None
                continue

            # Type checking the raw value against the required type of the input
            # Handle the edge case where the list has only one element
            list_types = [WorkflowInputType.LIST_STRING, WorkflowInputType.LIST_FILE]
            if defn.type in list_types and isinstance(raw_val, (str, int, float, Path)):
                raw_val = [raw_val]

            target_type = TYPE_MAP.get(defn.type, str)
            try:
                # This automatically handles:
                # - Path conversion
                # - String to Int/Bool
                # - List element validation
                adapter = TypeAdapter(target_type)
                validated[name] = adapter.validate_python(raw_val)

                # Extra check for Files/Dirs
                if defn.type == WorkflowInputType.FILE and not validated[name].is_file():
                    print(f"Warning: {name} path exists but is not a file.")
                if defn.type == WorkflowInputType.DIR and not validated[name].is_dir():
                    print(f"Warning: {name} path exists but is not a directory.")

            except Exception as e:
                raise TypeError(f"Input '{name}' failed validation for type {defn.type}: {e}")

        return validated

    @classmethod
    def from_yaml(cls, path: Path) -> "WorkflowManifest":
        """
        Utility function to create a WorkflowManifest object directly from reading a YAML file
        """
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls(**data)
