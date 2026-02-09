from typing import Any

import frontmatter

from myproject_core.agent import Agent

from .configs import Config, settings
from .schemas import AgentConfig, LLMModel, LLMProvider
from .utils import slugify


class AgentRegistry:
    def __init__(self, settings: Config):
        self.agent_dir = settings.path.agent_directory
        self.agents: dict[str, Agent] = {}
        self.settings = settings
        self.load_all()

    def load_all(self):
        """Scans the directory and populates the registry."""
        if not self.agent_dir.exists():
            return

        for md_file in self.agent_dir.glob("*.md"):
            try:
                agent_manifest = frontmatter.load(str(md_file))

                # Prepare the raw data dictionary from the markdown
                raw_data: dict[str, Any] = agent_manifest.metadata
                raw_data["system_prompt"] = agent_manifest.content.strip()
                if not raw_data.get("llm_config"):
                    raw_data["llm_config"] = self._get_llm_model_config()

                # Use model_validate to convert the dict into the AgentConfig object
                agent_config = AgentConfig.model_validate(raw_data)

                # Create the agent object
                self.agents[md_file.stem] = Agent(agent_config=agent_config)

            except Exception as e:
                print(f"Error loading agent manifest '{md_file.name}': {e}")

    def get_agent(self, name: str) -> Agent | None:
        return self.agents.get(name)

    def get_all_agents(self) -> dict[str, Agent]:
        return self.agents

    def _get_llm_model_config(self) -> LLMModel:
        base_url = self.settings.llm.base_url
        api_key = self.settings.llm.api_key
        llm_model = self.settings.llm.model
        return LLMModel(provider=LLMProvider(base_url=base_url, api_key=api_key), model=llm_model)


def main():
    agent_registry = AgentRegistry(settings=settings)
    print(agent_registry.get_all_agents())


if __name__ == "__main__":
    main()
