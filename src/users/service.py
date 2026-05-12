from fastapi import status, HTTPException
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from .models import User
from .utils import normalize_email
from src.auth.utils import hash_password
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
    async def get_user_by_google_sub(self, google_sub: str, session: AsyncSession) -> User | None:
        stmt = await session.execute(select(User).where(User.google_sub == google_sub))
        return stmt.scalar_one_or_none()
    
    async def handler_google_user(self, google_user: User, session: AsyncSession) -> User:
        if not google_user.google_sub:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Google payload: missing 'sub'."
            )
        exsting =  await self.get_user_by_google_sub(google_user.google_sub, session)
        if exsting:
            return exsting
        
        email_user = await user_service.get_user_by_email(google_user.email, session)
        if email_user:
            

