import uuid

from fastapi import HTTPException, status
from sqlalchemy import Integer, cast, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.utils import hash_password
from src.exceptions import UserNotFoundError
from src.monitor.models import Monitor
from src.probe.models import Probe

from .models import User
from .schemas import GoogleUser, UserCreate
from .utils import normalize_email


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

        new_user = User(
            email=email,
            hashed_password=hash_password(user_data.password),
            name=user_data.name,
        )

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


class AdminService:
    async def get_platform_stats(self, session: AsyncSession) -> dict:
        total_users = await session.scalar(select(func.count(User.id))) or 0
        total_monitors = await session.scalar(select(func.count(Monitor.id))) or 0
        total_probes = await session.scalar(select(func.count(Probe.id))) or 0

        probe_stmt = select(
            func.avg(cast(Probe.is_up, Integer)).label("uptime"),
            func.avg(Probe.latency_ms).label("avg_latency"),
        )
        probe_stats = (await session.execute(probe_stmt)).one()

        return {
            "total_users": total_users,
            "total_monitors": total_monitors,
            "total_probes_recorded": total_probes,
            "overall_uptime_percentage": round((probe_stats.uptime or 0.0) * 100, 2),
            "average_response_time": round(float(probe_stats.avg_latency or 0), 2),
        }

    async def get_users_with_monitor_count(self, session: AsyncSession) -> list[dict]:
        stmt = await session.execute(
            select(User, func.count(Monitor.id).label("monitor_count"))
            .outerjoin(Monitor, Monitor.owner_id == User.id)
            .group_by(User.id)
            .order_by(desc(User.created_at))
        )

        return [
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "role": user.role,
                "monitor_count": count,
                "created_at": user.created_at,
            }
            for user, count in stmt.all()
        ]

    async def delete_user(self, user_id: uuid.UUID, session: AsyncSession) -> None:
        user = await session.get(User, user_id)
        if not user:
            raise UserNotFoundError
        await session.delete(user)
        await session.flush()


admin_service = AdminService()
