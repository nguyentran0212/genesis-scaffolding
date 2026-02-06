import os
from pathlib import Path

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseModel):
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = Field(default=...)
    model: str = "openrouter/nvidia/nemotron-3-nano-30b-a3b:free"


class PathConfigs(BaseModel):
    working_directory: Path = Path(".")
    workspace_directory: Path = Path("./workspaces/")
    workflow_directory: Path = Path("./workflows/")

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

        # 3. Side-effect: Ensure they exist
        self.workspace_directory.mkdir(parents=True, exist_ok=True)
        self.workflow_directory.mkdir(parents=True, exist_ok=True)
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
