import uuid

from sqlalchemy import desc, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.monitor.schemas import MonitorCreate, MonitorUpdate

from ..exceptions import DuplicateMonitorError, MonitorNotFoundError
from .models import Monitor


class MonitorService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_monitor(self, data: MonitorCreate, user_id: uuid.UUID):
        logger.info(f"creating monitor for URL: {data.url}")
        new_monitor = Monitor(**data.model_dump(), owner_id=user_id)

        try:
            self.session.add(new_monitor)
            await self.session.commit()
            await self.session.refresh(new_monitor)
            return new_monitor

        except IntegrityError:
            await self.session.rollback()
            logger.warning(f"Duplicate monitor attempt: {data.url}")
            raise DuplicateMonitorError

    async def get_user_monitors(self, user_id: uuid.UUID) -> list[Monitor]:
        stmt = (
            select(Monitor)
            .where(Monitor.owner_id == user_id)
            .order_by(desc(Monitor.created_at))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_monitor_by_id(
        self, monitor_id: uuid.UUID, user_id: uuid.UUID
    ) -> Monitor:
        statement = await self.session.execute(
            select(Monitor).where(Monitor.id == monitor_id, Monitor.owner_id == user_id)
        )
        monitor = statement.scalar_one_or_none()
        if monitor is None:
            logger.info("monitor not found")
            raise MonitorNotFoundError
        return monitor

    async def update_monitor(
        self, monitor_id: uuid.UUID, user_id: uuid.UUID, data: MonitorUpdate
    ) -> Monitor:
        monitor = await self.get_monitor_by_id(monitor_id, user_id)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(monitor, key, value)

        await self.session.commit()
        await self.session.refresh(monitor)
        return monitor

    async def delete_monitor(self, monitor_id: uuid.UUID, user_id: uuid.UUID) -> None:
        monitor = await self.get_monitor_by_id(monitor_id, user_id)
        await self.session.delete(monitor)
        await self.session.commit()
        return

    async def get_user_stats(self, user_id: uuid.UUID) -> dict:
        stmt = await self.session.execute(
            select(
                func.count(Monitor.id).label("total_monitors"),
                func.count(Monitor.id)
                .filter(Monitor.is_active == True)
                .label("active_monitors"),
            ).where(Monitor.owner_id == user_id)
        )
        stats = stmt.one()

        return {}
