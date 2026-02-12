from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from myproject_core.configs import settings
from sqlmodel import Session, select

from ..auth.security import create_access_token, verify_password
from ..database import get_session
from ..models.user import User
from ..schemas.auth import Token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Annotated[Session, Depends(get_session)],
) -> Token:
    # Fetch user from DB
    statement = select(User).where(User.username == form_data.username)
    user = session.exec(statement).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.server.access_token_expire_minutes)
    access_token = create_access_token(subject=user.username, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")
