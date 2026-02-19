from pathlib import Path
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from myproject_core.agent_registry import AgentRegistry
from myproject_core.configs import settings
from myproject_core.workflow_engine import WorkflowEngine
from myproject_core.workflow_registry import WorkflowRegistry
from myproject_core.workspace import WorkspaceManager
from sqlmodel import Session, select

from .database import get_session
from .models.user import User
from .scheduler import SchedulerManager
from .schemas.auth import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


# --- Get current authenticated user ---
async def get_current_user(
    session: Annotated[Session, Depends(get_session)], token: Annotated[str, Depends(oauth2_scheme)]
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.server.jwt_secret_key, algorithms=[settings.server.algorithm])
        if not payload.get("sub"):
            raise credentials_exception
        username: str = str(payload.get("sub"))
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception

    # Query the actual database
    statement = select(User).where(User.username == token_data.username)
    user = session.exec(statement).first()

    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# --- Get the path to user's sandbox directory
async def get_user_inbox_path(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> Path:
    """
    Returns the resolved Path for the user's private inbox.
    Ensures the directory exists on disk.
    """
    user_path = settings.path.inbox_directory / str(current_user.id)
    user_path.mkdir(parents=True, exist_ok=True)
    return user_path


# --- Core Component Getters ---


def get_workflow_registry(request: Request) -> WorkflowRegistry:
    """Returns the registry, falling back to a new instance if not in state."""
    if hasattr(request.app.state, "workflow_registry"):
        return request.app.state.workflow_registry
    return WorkflowRegistry(settings)


def get_agent_registry(request: Request) -> AgentRegistry:
    if hasattr(request.app.state, "agent_registry"):
        return request.app.state.agent_registry
    return AgentRegistry(settings)


def get_workspace_manager(request: Request) -> WorkspaceManager:
    if hasattr(request.app.state, "wm"):
        return request.app.state.wm
    return WorkspaceManager(settings)


def get_workflow_engine(
    request: Request,
    wm: Annotated[WorkspaceManager, Depends(get_workspace_manager)],
    agent_reg: Annotated[AgentRegistry, Depends(get_agent_registry)],
) -> WorkflowEngine:
    if hasattr(request.app.state, "engine"):
        return request.app.state.engine
    return WorkflowEngine(wm, agent_reg)


def get_scheduler_manager(request: Request) -> SchedulerManager:
    """
    Dependency to retrieve the global scheduler manager from the app state.
    """
    return request.app.state.scheduler


# --- Type Aliases for Clean Routers ---

WorkflowRegDep = Annotated[WorkflowRegistry, Depends(get_workflow_registry)]
EngineDep = Annotated[WorkflowEngine, Depends(get_workflow_engine)]
