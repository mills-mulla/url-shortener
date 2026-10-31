import json
import logging

from datetime import datetime, timezone

from redis.asyncio import Redis

from app.config import settings

log = logging.getLogger(__name__)
MISS_TTL_SECONDS = 60

def _link_key(code: str) -> str:
    return f"link:{code}"

def _miss_key(code: str) -> str:
    return f"link:miss:{code}"

def ttl_for(expires_at: datetime | None,now: datetime | None = None) -> int:
    """
    seconds to cache a link: the defauilt ttl,but past expiry
    Return 0 if it has already expired (callers should skipp caching)
    """
    ttl = settings.cache_ttl_seconds
    if expires_at is None:
        return ttl
    now = now or datetime.now(timezone.utc)
    remaining = int((expires_at - now).total_seconds())
    return max(0,min(ttl, remaining))

async def get_link(redis: Redis, code: str) -> dict | None:
    """Cached link data, or None.Redis trouble counts as a miss not an error"""
    try:
        raw = await redis.get(_link_key(code))
        return json.loads(raw) if raw else None
    except Exception:
        log.warning("cache get failed for %s", code, exc_info=True)
        return None

async def set_link(redis: Redis, code: str, data: dict, ttl: int) -> None:
    if ttl <= 0:
        return
    try:
        await redis.set(_link_key(code), json.dumps(data), ex=ttl)
    except Exception:
        log.warning("cache set failed for %s", code, exc_info=True)    

async def is_miss(redis: Redis, code: str) -> None:
    """ True if recently learned the code does not exist """

    try:
        return bool(await redis.exists(_miss_key(code)))
    except Exception:
        log.warning("cache miss-check failed  for %s", code, exc_info=True)
        return False

async def set_miss(redis: Redis, code: str) -> None:
    try:
        await redis.set(_miss_key(code), "1", ex=MISS_TTL_SECONDS)
    except Exception:
        log.warning("cache set_miss failed for %s", code, exc_info=True)

async def invalidate(redis: Redis, code: str) -> None:
    """ Forget everything cahces about a specific code"""
    try:
        await redis.delete(_link_Key(code),_miss_Key(code))
    except Exception:
        log.warning("cache invalidate failed for %s", code,exc_info=True)