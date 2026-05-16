from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.db.session import get_session
from src.mail.dependency import get_mail_service
from src.mail.service import MailService
from src.users.schemas import UserCreate, UserLogin, UserResponse
from src.users.service import user_service

from .dependencies import get_current_user
from .schemas import PasswordResetConfirm, PasswordResetRequest, Token, TokenResponse
from .service import auth_service
from .utils import oauth

auth_router = APIRouter()
_security = HTTPBearer()
_session = Annotated[AsyncSession, Depends(get_session)]
_service = Annotated[MailService, Depends(get_mail_service)]


@auth_router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: UserCreate, mail_service: _service, session: _session):
    new_user = await user_service.create_user(payload, session)
    await mail_service.send_on_signup(new_user)

    return {"message": "Account created. Please verify your email to continue."}


@auth_router.post("/login")
async def login(payload: UserLogin, session: _session):
    user = await auth_service.authenticate_user(
        payload.email, payload.password, session
    )
    return auth_service.generate_token_pair(user)


@auth_router.post("/logout", status_code=status.HTTP_200_OK)
async def revoke_token(credentials: HTTPAuthorizationCredentials = Depends(_security)):
    return await auth_service.revoke_token(credentials.credentials)


@auth_router.post("/refresh", response_model=Token)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Depends(_security)):
    return await auth_service.refresh_tokens(credentials.credentials)


@auth_router.get("/me", response_model=UserResponse)
async def get_user(current_user=Depends(get_current_user)):
    return current_user


# verification/password routes
@auth_router.get("/verify-user/{token}")
async def verify_user(token: str, session: _session):
    return await auth_service.verify_user_account(token, session)


@auth_router.post("/request-password-reset/")
async def request_password_reset(payload: PasswordResetRequest, service: _service):
    return await service.send_password_reset(payload)


@auth_router.post("/reset-password/{token}")
async def reset_password(token: str, password: PasswordResetConfirm, session: _session):
    return await auth_service.password_reset(token, password, session)


# oauth routes
@auth_router.get("/google")
async def login_via_google(request: Request):
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)  # type: ignore


@auth_router.get("/callback/google")
async def google_callback(request: Request, session: _session):
    return await auth_service.oauth_callback(request, session)
