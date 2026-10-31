import asyncio
import logging
import socket
from datetime import datetime

import redis.asyncio as aioredis
from redis.exceptions import ResponseError
from sqlalchemy import insert
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.config import settings
from app.models import Click
from worker.parsing import hash_ip, parse_device, referrer_host

log = logging.getLogger(__name__)

GROUP = "click-worker"
CONSUMER = f"worker-{socket.gethostname()}"
BATCH = 100
BLOCK_MS = 2000
CLAIM_IDLE_MS = 60_000


def to_click_row(field: dict[str, str]) -> dict:
    """
    Turn one stream entry into a row for the clicks table.raisees on bad data.
    """
    device, browser = parse_device(fields.get("ua") or None)
    ip24 = field.get("ip24") or ""
    return {
        "link_id": int(fields["link_id"]),
        "ts": datetime.fromisoformat(fields["ts"]),
        "referrer": referrer_host(fields.get("referrer") or None),
        "device": (device or "other")[:16],
        "browser": browser[:64] if browser else None,
        "country": None, #Geoip will come later
        "ip_hash": hash_ip(ip24, settings.ip_hash_salt) if ip24 else None,
    }

async def process_batch(engine: AsyncEngine, redis, entries) -> int:
    rows,ids = [], []
    for entry_id, fields in entries:
        ids.append(entry_id)
        if not fields:
            continue
        try:
            rows.append(to_click_row(fields))
        except Exception:
            log.warning("skipping malformed event %s", entry_id, exec_info=True)

    if rows:
        await _insert(engine, rows)
    if ids:
        await redis.xack(settings.stream_name, GROUP, *ids)
    return len(rows)

async def ensure_group(redis) -> None:
    try:
        await redis.xgroup_create(settings.stream_name, GROUP, id="0", mkstream=True)
    except ResponseError as exc:
        if "BUSYGROUP" not in str(exc):
            raise
        
async def read_entries(redis):
    # 1) takeover entries a crashed worker left unacknowledged
    claimed = await redis.xautoclaim(
        settings.stream_name,
        GROUP,
        CONSUMER,
        min_idle_time=CLAIM_IDLE_MS,
        start_id="0-0",
        count=BATCH,
    )   
    if claimed[1]:
        return claimed[1]
        #ortherwise wait for new entries
    resp = await redis.xreadgroup(
        GROUP, CONSUMER, {settings.stream_name: ">"}, count=BATCH,block=BLOCK_MS
    )
    return resp[0][1] if  resp else []

async def run() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
    )
    redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    engine = create_async_engine(settings.database_url,pool_pre_ping=True)
    await ensure_group(redis)
    log.info("worker %s started", CONSUMER)
    try:
        while True:
            try:
                entries = await read_entries(redis)
                if entries:
                    n = await process_batch(engine, redis, entries)
                    log.info("stored %d clicks", n)
            except Exception:
                log.exception("batch failed, retrying in 5s")
                await asyncio.sleep(5)
    finally:
        await redis.aclose()
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(run())