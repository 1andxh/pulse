import asyncio
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI

from src.auth.routes import auth_router
from src.core.health import health

# from src.core.sentry import sentry
from src.core.worker import worker

# from src.dashboard.routes import dashboard_router
from src.db.base import Base as Base
from src.db.session import engine
from src.monitor.routes import monitor_router
from src.probe.routes import probe_router
from src.public_tools.routes import tool_router
from src.users.routes import admin_router

from .exception_handler import (
    PulseError,
    RequestValidationError,
    general_exception_handler,
    pulse_exception_handler,
    validation_exception_handler,
)
from .middleware import register_middleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = httpx.AsyncClient()
    app.state.http_client = client

    task = asyncio.create_task(worker(client, app))

    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        await client.aclose()
        await engine.dispose()


app = FastAPI(
    title="Probey",
    lifespan=lifespan,
    description="A lightweight, reliable uptime monitor",
    openapi_url="/docs/openapi.json",
)

# exceptions
app.add_exception_handler(PulseError, pulse_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# middleware
register_middleware(app)

# routes
# app.include_router(sentry, tags=["logs"])
app.include_router(health, tags=["health-checks"])
app.include_router(monitor_router, tags=["monitors"], prefix="/monitors")
app.include_router(probe_router, tags=["probes"], prefix="/history")
# app.include_router(dashboard_router, tags=["dashboard"])
app.include_router(tool_router, tags=["public-tools"])
app.include_router(auth_router, tags=["authentication"], prefix="/auth")
app.include_router(admin_router, tags=["admin"], prefix="/admin")


__all__ = [
    "health",
    "Base",
    "worker",
    "engine",
    "monitor_router",
    # "dashboard_router",
    "probe_router",
    "tool_router",
    "auth_router",
    "admin_router",
]
