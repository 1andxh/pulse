import redis
from src.config import settings

redis_client = redis.from_url(url=settings.redis_url, decode_responses=True)


class RateLimiter:
    def __init__(self, client: redis.Redis):
        self.client = client

    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        current_usage = self.client.incr(key)

        if current_usage == 1:
            self.client.expire(key, window)

        return current_usage <= limit


rate_limiter = RateLimiter(redis_client)
