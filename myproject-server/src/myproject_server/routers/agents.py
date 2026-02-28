from typing import List

from fastapi import APIRouter, Depends, HTTPException
from myproject_core.agent_registry import AgentRegistry

from ..dependencies import get_agent_registry
from ..schemas.agent import AgentRead

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/", response_model=List[AgentRead])
async def list_agents(agent_reg: AgentRegistry = Depends(get_agent_registry)):
    """
    Returns a list of all available agents blueprints.
    """
    results = []
    for id, blueprint in agent_reg.blueprints.items():
        results.append(
            AgentRead(
                id=id,
                name=blueprint.name,
                description=blueprint.description,
                interactive=blueprint.interactive,
                allowed_tools=blueprint.allowed_tools,
                allowed_agents=blueprint.allowed_agents,
                model_name=blueprint.llm_config.model if blueprint.llm_config else None,
            )
        )
    return results


@router.get("/{agent_id}", response_model=AgentRead)
async def get_agent_details(agent_id: str, agent_reg: AgentRegistry = Depends(get_agent_registry)):
    """
    Returns the full metadata for a specific agent.
    """
    blueprint = agent_reg.blueprints.get(agent_id)
    if not blueprint:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found in registry.")

    return AgentRead(
        id=agent_id,
        name=blueprint.name,
        description=blueprint.description,
        interactive=blueprint.interactive,
        allowed_tools=blueprint.allowed_tools,
        allowed_agents=blueprint.allowed_agents,
        model_name=blueprint.llm_config.model if blueprint.llm_config else None,
    )
