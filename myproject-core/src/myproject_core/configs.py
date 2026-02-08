import os
from pathlib import Path

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseModel):
    # URL of the model provider backend. Default to openrouter
    base_url: str = "https://openrouter.ai/api/v1"
    # API key for accessing the model provider backend. Required
    api_key: str = Field(default=...)
    # Identifier of the model at the provider backend.
    model: str = "openrouter/nvidia/nemotron-3-nano-30b-a3b:free"


class PathConfigs(BaseModel):
    # Path to working directory. Default to current working directory.
    working_directory: Path = Path(".")
    # Path to workspace directory that stores job directories of workflows
    workspace_directory: Path = Path("./workspaces/")
    # Path to workflow directory that stores YAML manifest files of workflows
    workflow_directory: Path = Path("./workflows/")
    # Path to a directory where user can drop input files for workflows
    inbox_directory: Path = Path("./inbox/")

    @model_validator(mode="after")
    def resolve_paths(self) -> "PathConfigs":
        # 1. Resolve Working Directory
        if self.working_directory is None:
            self.working_directory = Path.cwd().resolve()
        else:
            self.working_directory = self.working_directory.resolve()

        # 2. Create workspace and workflow directories underneath working directory
        self.workspace_directory = self.working_directory / "workspaces"
        self.workflow_directory = self.working_directory / "workflows"
        self.inbox_directory = self.workflow_directory / "inbox"

        # 3. Side-effect: Ensure they exist
        self.workspace_directory.mkdir(parents=True, exist_ok=True)
        self.workflow_directory.mkdir(parents=True, exist_ok=True)
        self.inbox_directory.mkdir(parents=True, exist_ok=True)
        return self


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="myproject_",
        env_file=[".env", ".env.prod"],
        env_nested_delimiter="_",
        env_nested_max_split=1,
    )

    llm: LLMConfig
    path: PathConfigs = Field(default_factory=PathConfigs)


# Create the singleton instance
settings = Config()  # pyright: ignore[reportCallIssue]


def main():
    print(os.getcwd())
    print(settings.model_dump_json())


if __name__ == "__main__":
    main()
