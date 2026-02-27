from pathlib import Path

import frontmatter

from myproject_core.agent import Agent
from myproject_tools import registry

from .agent_memory import AgentMemory
from .configs import Config, settings
from .schemas import AgentConfig, LLMModel, LLMProvider


class AgentRegistry:
    def __init__(self, settings: Config):
        self.agent_dir = settings.path.agent_directory
        self.settings = settings
        # Store CONFIGS (blueprints), not INSTANCES
        self.blueprints: dict[str, AgentConfig] = {}
        self.load_all()

    def load_all(self):
        """Scans directory and stores the blueprints."""
        if not self.agent_dir.exists():
            return

        for md_file in self.agent_dir.glob("*.md"):
            try:
                agent_manifest = frontmatter.load(str(md_file))
                raw_data = agent_manifest.metadata
                raw_data["system_prompt"] = agent_manifest.content.strip()

                if not raw_data.get("llm_config"):
                    raw_data["llm_config"] = self._get_llm_model_config()

                config = AgentConfig.model_validate(raw_data)
                # Store the name from the file stem or manifest
                self.blueprints[md_file.stem] = config
            except Exception as e:
                print(f"Error loading {md_file.name}: {e}")

    def create_agent(
        self,
        name: str,
        working_directory: Path | None = None,
        memory: AgentMemory | None = None,
        **overrides,
    ) -> Agent:
        """Factory method to spawn a fresh agent instance."""
        blueprint = self.blueprints.get(name)
        if not blueprint:
            raise ValueError(f"Agent '{name}' not found in registry.")

        # Optional: Allow overriding config values at runtime
        # We deepcopy to ensure we don't mutate the original blueprint
        instance_config = blueprint.model_copy(deep=True, update=overrides)

        return Agent(agent_config=instance_config, working_directory=working_directory, memory=memory)

    def get_all_agent_types(self):
        return self.blueprints.keys()

    def _get_llm_model_config(self) -> LLMModel:
        base_url = self.settings.llm.base_url
        api_key = self.settings.llm.api_key
        llm_model = self.settings.llm.model
        return LLMModel(provider=LLMProvider(base_url=base_url, api_key=api_key), model=llm_model)


def main():
    agent_registry = AgentRegistry(settings=settings)
    print(agent_registry.get_all_agent_types())


if __name__ == "__main__":
    main()
