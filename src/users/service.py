from fastapi import status, HTTPException
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User
from .utils import normalize_email
from src.auth.utils import (
    ACCESS_TOKEN_EXPIRY,
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)
from .schemas import UserCreate

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

        new_user = User(email=email, hashed_password=user_data.password)

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
