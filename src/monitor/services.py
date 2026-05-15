import uuid

from sqlalchemy import desc, select, func, cast, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.monitor.schemas import MonitorCreate, MonitorUpdate

from ..exceptions import DuplicateMonitorError, MonitorNotFoundError
from .models import Monitor
from src.probe.models import Probe


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
        monitor_stmt = select(
            func.count(Monitor.id).label("total_monitors"),
            func.count(Monitor.id)
            .filter(Monitor.is_active == True)
            .label("active_monitors"),
        ).where(Monitor.owner_id == user_id)
        stats = (await self.session.execute(monitor_stmt)).one()

        probe_stmt = (
            select(
                func.avg(cast(Probe.is_up, Integer)).label("uptime"),
                func.avg(Probe.latency_ms).label("avg_latency"),
            )
            .join(Monitor, Probe.monitor_id == Monitor.id)
            .where(Monitor.owner_id == user_id)
        )
        uptime = (await self.session.execute(probe_stmt)).one()

        return {
            "total_monitors": stats.total_monitors,
            "active_monitors": stats.active_monitors,
            "uptime_percentage": round((uptime.uptime or 0.0) * 100, 2),
            "average_response_time": round(float(uptime.avg_latency or 0), 2),
        }

    async def get_all_active_monitors(self) -> list[Monitor]:
        stmt = await self.session.execute(
            select(Monitor).where(Monitor.is_active == True)
        )
        return list(stmt.scalars().all())
