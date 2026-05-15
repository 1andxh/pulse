import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_session
from .schemas import ProbeHistoryResponse
from .services import ProbeService
from src.monitor.dependency import get_monitor_service
from src.monitor.services import MonitorService
from src.users.models import User
from src.auth.dependencies import get_current_verified_user

probe_router = APIRouter()


async def _get_probe_service(
    session: AsyncSession = Depends(get_session),
    monitor_service: MonitorService = Depends(get_monitor_service),
) -> ProbeService:
    return ProbeService(session, monitor_service)


@probe_router.get("/{monitor_id}/", response_model=ProbeHistoryResponse)
async def get_probe_history(
    monitor_id: uuid.UUID,
    service: Annotated[ProbeService, Depends(_get_probe_service)],
    curent_user: User = Depends(get_current_verified_user),
):
    return await service.get_latest_probes(monitor_id, curent_user.id)
