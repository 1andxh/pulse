import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status

from .dependency import get_monitor_service
from .schemas import MonitorCreate, MonitorRead, MonitorUpdate, StatsResponse
from .services import MonitorService
from src.auth.dependencies import get_current_verified_user
from src.users.models import User

_service = Annotated[MonitorService, Depends(get_monitor_service)]
_current_user = Annotated[User, Depends(get_current_verified_user)]

monitor_router = APIRouter()


# stats route
@monitor_router.get("/stats", response_model=StatsResponse)
async def get_stats(current_user: _current_user, service: _service):
    return await service.get_user_stats(current_user.id)


@monitor_router.post(
    "/", status_code=status.HTTP_201_CREATED, response_model=MonitorRead
)
async def create_monitor_route(
    payload: MonitorCreate, current_user: _current_user, service: _service
):
    monitor = await service.create_monitor(payload, current_user.id)
    return monitor


@monitor_router.get("/{monitor_id}", response_model=MonitorRead)
async def get_monitor(
    monitor_id: uuid.UUID, current_user: _current_user, service: _service
):
    return await service.get_monitor_by_id(monitor_id, current_user.id)


@monitor_router.get("/", response_model=list[MonitorRead])
async def list_monitors(current_user: _current_user, service: _service):
    monitors = await service.get_user_monitors(current_user.id)
    return monitors


@monitor_router.patch("/{monitor_id}", response_model=MonitorRead)
async def update_monitor(
    monitor_id: uuid.UUID,
    payload: MonitorUpdate,
    current_user: _current_user,
    service: _service,
):
    return await service.update_monitor(monitor_id, current_user.id, payload)


@monitor_router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_monitor(
    monitor_id: uuid.UUID, current_user: _current_user, service: _service
):
    return await service.delete_monitor(monitor_id, current_user.id)
