from fastapi import APIRouter , Depends, HTTPException,Header
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_db
from app.models import User
from app.services.security import hash_key

_redis:Redis | None = None

def get_redis() -> Redis:
    """one shared redis client for the whole app"""
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis

async def current_user(
    x_api_key:str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
    ) -> User:
    """return the user who owns the x-api-key header or raise 401 """
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
  
    result = await db.execute(
        select(User).where(User.api_key_hash == hash_key(x_api_key))
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return user
    