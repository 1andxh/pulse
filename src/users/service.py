from fastapi import status, HTTPException
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User
from .utils import normalize_email
from src.auth.utils import hash_password
from .schemas import UserCreate, GoogleUser
from src.auth.schemas import PasswordResetConfirm

REFRESH_TOKEN_EXPIRY_DAYS = 7


class UserService:
    async def _get_user_by_email(
        self, email: str, session: AsyncSession
    ) -> User | None:
        normalized_email = normalize_email(email)
        stmt = await session.execute(select(User).where(User.email == normalized_email))
        return stmt.scalar_one_or_none()

    async def _verify_user(self, user: User, session: AsyncSession) -> User:
        user.is_verified = True
        await session.flush()
        await session.refresh(user)
        return user

    async def _reset_password(
        self,
        user: User,
        new_password: str,
        session: AsyncSession,
    ) -> User | None:
        user.hashed_password = new_password
        await session.flush()
        await session.refresh(user)
        return user

    async def get_user_by_email(self, email: str, session: AsyncSession) -> User | None:
        return await self._get_user_by_email(email, session)

    async def check_user_exists(self, email: str, session: AsyncSession) -> bool:
        return await self.get_user_by_email(email, session) is not None

    async def create_user(self, user_data: UserCreate, session: AsyncSession) -> User:
        email = normalize_email(user_data.email)
        if await self.check_user_exists(email, session):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        new_user = User(email=email, hashed_password=hash_password(user_data.password))

        session.add(new_user)

        try:
            await session.flush()
            await session.refresh(new_user)
        except IntegrityError:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )
        return new_user


user_service = UserService()


class OAuthService:
    async def get_user_by_google_sub(
        self, google_sub: str, session: AsyncSession
    ) -> User | None:
        stmt = await session.execute(select(User).where(User.google_sub == google_sub))
        return stmt.scalar_one_or_none()

    async def handler_google_user(
        self, google_user: GoogleUser, session: AsyncSession
    ) -> User:
        exsting = await self.get_user_by_google_sub(google_user.google_sub, session)
        if exsting:
            return exsting

        email_user = await user_service.get_user_by_email(google_user.email, session)
        if email_user:
            email_user.google_sub = google_user.google_sub
            email_user.is_verified = True
            email_user.auth_provider = "google"

            await session.flush()
            await session.refresh(email_user)
            return email_user

        new_user = User(
            email=google_user.email,
            full_name=google_user.name,
            google_sub=google_user.google_sub,
            is_verified=True,
            auth_provider="google",
            hashed_password=None,
        )

        session.add(new_user)
        await session.flush()
        await session.refresh(new_user)
        return new_user


oauth_service = OAuthService()
