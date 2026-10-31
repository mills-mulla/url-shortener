import re
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from redis.asyncio import Redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_db

from app.deps import get_redis
from app.models import Link
from app.services import caches

router = APIRouter(tags=["redirect"])

CODE_RE = re.compile(r"[A-Za-z0-9_-]{4,32}")

@router.get("/{code}")
async def redirect(
    code: str,
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
):
    if not CODE_RE.fullmatch(code):
        raise HTTPException(status_code=404, detail="Not found")
    data = await caches.get_link(redis, code)

    if data is None:
        if await caches.is_miss(redis, code):
            raise HTTPException(status_code=404, detail="Not found")
        
        result = await db.execute(select(Link).where(Link.code == code))
        link = result.scalar_one_or_none()
        if link is None:
            await caches.set_miss(redis, code)
            raise HTTPException(status_code=404, detail="Not found")
        data = {
            "id": link.id,
            "url": link.target_url,
            "is_active": link.is_active,
            "expires_at": link.expires_at.isoformat() if link.expires_at else None,
        }

        await caches.set_link(redis, code, data, caches.ttl_for(link.expires_at))
    if not data["is_active"]:
        raise HTTPException(status_code=410, detail="Link is disabled")

    expires_at = data["expires_at"]
    if expires_at and datetime.fromisoformat(expires_at) <= datetime.now(timezone.utc):
         raise HTTPException(status_code=410, detail="Link has expired")
    
    return RedirectResponse(data["url"],status_code=302)
