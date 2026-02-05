from pydantic import BaseModel, Field

from pydantic_settings import BaseSettings, SettingsConfigDict

import os

class LLMConfig(BaseModel):
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = Field(default=...)
    model: str = "openrouter/nvidia/nemotron-3-nano-30b-a3b:free"

class Config(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="myproject_", env_file=[".env", ".env.prod"], env_nested_delimiter="_", env_nested_max_split=1)

    llm: LLMConfig

# Create the singleton instance
settings = Config()  # pyright: ignore[reportCallIssue]

if __name__ == "__main__":
    print(os.getcwd())
    print(settings.model_dump_json())
