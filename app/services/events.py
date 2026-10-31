import logging
from datetime import datetime, timezone

from fastapi import Request
from redis.asyncio import Redis

from app.config import settings
from worker.parsing import truncate_ip

log = logging.getLogger(__name__)

MAX_REFERRER = 2048
MAX_UA = 512

def build_click_event(
    link_id: int,
    referrer: str | None,
    user_agent: str | None,
    client_ip: str | None,
    now: datetime,
) -> dict[str,str]:
    if now.tzinfo is None:
        raise ValueError("nowmust be timezone-aware")
    try:
        ip24 = truncate_ip(client_ip) if client_ip else ""
    except ValueError:
        ip24 = ""
    return {
        "link_id": str(link_id),
        "ts": now.astimezone(timezone.utc).isoformat(),
        "referrer": (referrer or "")[:MAX_REFERRER],
        "ua": (user_agent or "")[:MAX_UA],
        "ip24": ip24,
    }
async def publish_click(redis: Redis,link_id: int, request: Request) -> None:
    """ queue a click event.Never raises: Redirect must not failover analytics"""
    try:
        event = build_click_event(
            link_id,
            request.headers.get("referrer"),
            request.headers.get("user-agent"),
            request.client.host if request.client else None,
            datetime.now(timezone.utc),
        )
        await redis.xadd(
            setting.stream_name,
            event,
            maxlen=settings.stream_maxlen,
            approximate=True,
        )
    except Exception:
        log.warning("click publish failed", exc_info=True)