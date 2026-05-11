from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.users.models import User
from .utils import (
    create_access_token,
    verify_password,
    ACCESS_TOKEN_EXPIRY,
    REFRESH_TOKEN_EXPIRY_DAYS,
    decode_token,
)
from .schemas import Token
from datetime import timedelta, datetime, timezone
from src.users.service import UserService
from src.core.redis import token_blocklist

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
