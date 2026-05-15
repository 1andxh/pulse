from datetime import datetime, timedelta, timezone

from authlib.integrations.starlette_client import OAuthError
from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.redis import token_blocklist
from src.mail.utils import mail_utils
from src.users.models import User
from src.users.schemas import GoogleUser
from src.users.service import UserService, oauth_service

from .schemas import PasswordResetConfirm, Token
from .utils import (
    ACCESS_TOKEN_EXPIRY,
    REFRESH_TOKEN_EXPIRY_DAYS,
    create_access_token,
    decode_token,
    hash_password,
    oauth,
    verify_password,
)

service = UserService()


class AuthService:
    def _build_token_payload(self, user: User) -> dict:
        return {"email": user.email, "user_id": str(user.id)}

    def generate_token_pair(self, user: User) -> Token:
        payload = self._build_token_payload(user)

        access_token = create_access_token(
            payload, expiry=timedelta(seconds=ACCESS_TOKEN_EXPIRY), refresh=False
        )
        refresh_token = create_access_token(
            payload, expiry=timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS), refresh=True
        )
        return Token(access_token=access_token, refresh_token=refresh_token)

    async def authenticate_user(
        self, email: str, password: str, session: AsyncSession
    ) -> User:
        user = await service._get_user_by_email(email, session)
        if user is None or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        return user

    async def refresh_tokens(self, refresh_token: str) -> Token:
        payload = decode_token(refresh_token)

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )

        if not payload.get("refresh", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token required",
            )

        jti = payload.get("jti")
        if not jti:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        if await token_blocklist.token_in_blocklist(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has been revoked",
            )

        user_data = payload.get("user") or {}
        email = user_data.get("email")
        user_id = user_data.get("user_id")

        if not email or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        remaining_ttl = max(
            1, int(payload["exp"] - datetime.now(timezone.utc).timestamp())
        )
        await token_blocklist.add_token_to_blocklist(jti, expiry=remaining_ttl)

        new_payload = {"email": email, "user_id": user_id}

        return Token(
            access_token=create_access_token(user_data=new_payload, refresh=False),
            refresh_token=create_access_token(
                user_data=new_payload,
                expiry=timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS),
                refresh=True,
            ),
        )

    async def revoke_token(self, token: str) -> dict:
        payload = decode_token(token)
        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        jti = payload.get("jti")
        if jti:
            token_expiry = max(
                1, int(payload["exp"] - datetime.now(timezone.utc).timestamp())
            )
            await token_blocklist.add_token_to_blocklist(jti, token_expiry)
        return {"message": "logged out"}

    async def get_current_user(self, token: str, session: AsyncSession) -> User:
        payload = decode_token(token)

        if payload is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
            )
        if payload.get("refresh", False):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Access token required",
            )

        user_data = payload.get("user") or {}
        email = user_data.get("email")

        if not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
            )

        user = await service.get_user_by_email(email, session)
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )

        return user

    async def oauth_callback(self, request: Request, session: AsyncSession):
        try:
            token = await oauth.google.authorize_access_token(request)  # type: ignore
        except OAuthError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Google authentication failed",
            )

        userinfo = token.get("userinfo")
        if not userinfo:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not retrieve user info from Google",
            )

        google_user = GoogleUser(**userinfo)
        user = await oauth_service.handler_google_user(google_user, session)
        tokens = auth_service.generate_token_pair(user)

        redirect = RedirectResponse(
            url=f"{settings.frontend_url}/auth/callback?access_token={tokens.access_token}&refresh_token={tokens.refresh_token}"
        )
        return redirect

    async def verify_user_account(self, token: str, session: AsyncSession):
        token_data = mail_utils.decode_url_safe_token(
            token, mail_utils.email_serializer
        )
        email = token_data.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token",
            )

        user = await service.get_user_by_email(email, session)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        if user.is_verified:
            return {"message": "Account already verified"}

        await service._verify_user(user, session)
        return {"message": "Account verified successfully"}

    async def password_reset(
        self, token: str, password: PasswordResetConfirm, session: AsyncSession
    ):
        token_data = mail_utils.decode_url_safe_token(
            token, mail_utils.password_reset_serializer
        )
        if token_data.get("type") != "password-reset":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password reset token",
            )
        email = token_data.get("email")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password reset token",
            )
        user = await service.get_user_by_email(email, session)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Could not veirfy user"
            )

        if password.new_password != password.confirm_new_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match"
            )
        password_hash = hash_password(password.new_password)
        await service._reset_password(
            user,
            password_hash,
            session,
        )
        return ({"message": "Password reset successful"},)


auth_service = AuthService()
