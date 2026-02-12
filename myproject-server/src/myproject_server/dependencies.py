from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from myproject_core.configs import settings
from sqlmodel import Session, select

from .database import get_session
from .models.user import User
from .schemas.auth import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


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
