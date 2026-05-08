from fastapi import Request
import httpx
import time
from ..core.redis import rate_limiter
from ..exceptions import RateLimitExceeded
from .utils import normalize_public_url


async def get_quick_check(req: Request, url: str):
    client_ip = req.client.host if req.client else None
    key = f"rate_limit:{client_ip}"

    if not rate_limiter.is_allowed(key, limit=5, window=60):
        raise RateLimitExceeded

    clean_url = normalize_public_url(url)

    async with httpx.AsyncClient() as client:
        start_time = time.perf_counter()
        try:
            response = await client.get(clean_url, timeout=5)
            latency = round((time.perf_counter() - start_time) * 1000, 2)

            return {
                "url": clean_url,
                "status_code": response.status_code,
                "latency_ms": latency,
                "is_up": response.status_code < 400,
            }
        except Exception as e:
            return {"url": clean_url, "is_up": False, "error": str(e)}
