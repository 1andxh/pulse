import redis.asyncio as redis
from datetime import timedelta

from src.config import settings

redis_client = redis.from_url(url=settings.redis_url, decode_responses=True)


class RateLimiter:

    _RATE_LIMIT = """
        local current = redis.call("INCR", KEYS[1])
        if current == 1 then
            redis.call("EXPIRE", KEYS[1], ARGV[1])
        end
        return current
"""

    def __init__(self, client: redis.Redis):
        self.client = client
        self._script = self.client.register_script(self._RATE_LIMIT)

    async def is_allowed(self, key: str, limit: int, window: int) -> bool:
        current = int(await self._script(keys=[key], args=[window]))
        return current <= limit

    async def remaining(self, key: str, limit: int) -> int:
        current = await self.client.get(key)
        if current is None:
            return limit
        return max(0, limit - int(current))

    async def reset(self, key) -> None:
        await self.client.delete(key)


rate_limiter = RateLimiter(redis_client)


class TokenBlockList:
    JTI_EXPIRY = timedelta(days=7)

    def __init__(self, blocklist: redis.Redis):
        self.blocklist = blocklist

    async def add_token_to_blocklist(self, jti: str, expiry: int | None = None) -> None:
        ttl = expiry if expiry and expiry > 0 else self.JTI_EXPIRY
        await self.blocklist.set(name=jti, value="", ex=ttl)

    async def token_in_blocklist(self, jti: str) -> bool:
        return await self.blocklist.get(name=jti) is not None


token_blocklist = TokenBlockList(redis_client)
