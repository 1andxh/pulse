from fastapi import APIRouter, Depends, status, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from src.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from .service import auth_service
from .dependencies import get_current_verified_user, get_current_user
from src.users.models import User
from src.users.schemas import UserCreate, UserLogin, UserResponse
from src.users.service import user_service
from .schemas import Token

from typing import Annotated
from src.config import settings

auth_router = APIRouter()
_security = HTTPBearer()
_session = Annotated[AsyncSession, Depends(get_session)]


@auth_router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register(payload: UserCreate, session: _session):
    new_user = await user_service.create_user(payload, session)
    return new_user


@auth_router.post("/login")
async def login(payload: UserLogin, session: _session):
    user = await auth_service.authenticate_user(
        payload.email, payload.password, session
    )
    return auth_service.generate_token_pair(user)


@auth_router.post("/logout", status_code=status.HTTP_200_OK)
async def revoke_token(credentials: HTTPAuthorizationCredentials = Depends(_security)):
    return await auth_service.revoke_token(credentials.credentials)


@auth_router.post("/refresh")
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(_security)):
    return await auth_service.refresh_tokens(credentials.credentials)


@auth_router.get("/me", response_model=UserResponse)
async def get_user(current_user=Depends(get_current_user)):
    return current_user


# oauth routes
@auth_router.get("/google")
async def login_via_google(request: Request):
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)  # type: ignore


@auth_router.get("/callback/google")
async def google_callback(request: Request, session: _session):
    return await auth_service.oauth_callback(request, session)


#
