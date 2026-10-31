import logging
import time

from redis.asyncio import Redis

log = logging.getLogger(__name__)

async def hit( redis: Redis, key: str, limit: int,window_s: int, now: float | None = None) -> tuple[bool,int]:
    """
    fixed window limiter Returns(allowed_seconds_until_the_window_resets).
    If Redis is down we allow the request (fail open).
    """
    now = time.time() if now is None else now
    window = int(now // window_s)
    retry_after = window_s - int(now % window_s)
    redis_key = f"rl:{key}:{window}"

    try:
        async with redis.pipeline() as pipe:
            pipe.incr(redis_key)
            pipe.expire(redis_key,window_s + 5)
            results = await pipe.execute()
            count = results[0]

    except Exception:
        log.warning("rate limit check failed", exc_info=True)
        return True, 0
    return count <= limit, retry_after