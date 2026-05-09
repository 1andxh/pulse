import asyncio
from datetime import datetime, timezone

import httpx
from fastapi import FastAPI

from src.core.logger import logger
from src.db.session import AsyncSessionLocal
from src.monitor.services import MonitorService
from src.probe import Probe

from .checker import CheckResult, check_monitor, is_monitor_due


async def worker(client: httpx.AsyncClient, app: FastAPI):
    try:
        while True:
            now = datetime.now(timezone.utc)

            app.state.worker_last_seen = now

            async with AsyncSessionLocal() as session:
                service = MonitorService(session)
                monitors = await service.get_all_monitors()

                due_monitors = [
                    monitor for monitor in monitors if is_monitor_due(monitor, now)
                ]
                if not due_monitors:
                    logger.debug("no monitors due, skipping check cycle")

                    await asyncio.sleep(3)
                    continue
                logger.info(f"checking {len(due_monitors)} monitor(s)")

                tasks = [check_monitor(monitor, client) for monitor in due_monitors]

                results = await asyncio.gather(*tasks, return_exceptions=True)

                for monitor, result in zip(due_monitors, results):
                    if isinstance(result, Exception):
                        normalized = CheckResult(
                            is_up=False, latency_ms=None, error_message=str(result)
                        )
                    else:
                        normalized = result

                    probe = Probe(
                        monitor_id=monitor.id,
                        latency_ms=normalized.latency_ms,
                        is_up=normalized.is_up,
                        error_message=normalized.error_message,
                    )
                    monitor.last_checked_at = now
                    session.add(probe)

                await session.commit()
                logger.info(f"Successfully processed {len(due_monitors)} probe(s)")

            await asyncio.sleep(1)
    except asyncio.CancelledError:
        logger.info("worker shutting down..")
        raise

    except Exception:
        logger.error("worker crashed", exc_info=True)
        await asyncio.sleep(5)
