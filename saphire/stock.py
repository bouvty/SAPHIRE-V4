import asyncio
import logging
from datetime import datetime, timezone
import asyncpg
import httpx
from .settings import settings

class StockStore:
    def __init__(self):
        self.pool = None
    async def connect(self):
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is required")
        self.pool = await asyncpg.create_pool(dsn=settings.database_url, min_size=1, max_size=4)
        async with self.pool.acquire() as c:
            await c.fetchval("SELECT id FROM public.stock_members WHERE id=1")
    async def close(self):
        if self.pool:
            await self.pool.close()
    async def get(self):
        async with self.pool.acquire() as c:
            row = await c.fetchrow("SELECT online_members,offline_members,updated_at FROM public.stock_members WHERE id=1")
        return dict(row) if row else None
    async def save(self,online,offline):
        async with self.pool.acquire() as c:
            return await c.execute("""INSERT INTO public.stock_members(id,online_members,offline_members,updated_at) VALUES(1,$1,$2,now())
                ON CONFLICT(id) DO UPDATE SET online_members=excluded.online_members,
                offline_members=excluded.offline_members,updated_at=excluded.updated_at""",online,offline)

async def fetch_stock(client):
    response = await client.get(settings.stock_source_url)
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload,dict) or payload.get("success") is not True:
        raise ValueError("Stock source returned unsuccessful response")
    online,offline = payload.get("online_members"),payload.get("offline_members")
    if any(type(v) is not int or v < 0 for v in (online,offline)):
        raise ValueError("Invalid stock count; expected nonnegative integers")
    return online, offline

async def sync_loop(store, stop):
    interval = max(30, settings.stock_refresh_seconds)
    async with httpx.AsyncClient(timeout=settings.stock_request_timeout_seconds,follow_redirects=False) as client:
        while not stop.is_set():
            try:
                online,offline = await fetch_stock(client)
                await store.save(online,offline)
                logging.log(25,"Stock synced | online=%s offline=%s",online,offline)
            except Exception as exc:
                logging.error("Stock sync failed: %s",exc)
            try: await asyncio.wait_for(stop.wait(),timeout=interval)
            except asyncio.TimeoutError: pass

def relative_stamp(dt):
    return f"<t:{int(dt.timestamp())}:R>" if dt else "Not synchronized"
def countdown(seconds):
    minutes,seconds = divmod(max(0,int(seconds)),60)
    return f"{minutes}m {seconds:02d}s" if minutes else f"{seconds}s"
def stock_payload(row):
    if not row:
        return {"success":False,"online_members":0,"offline_members":0,"last_updated":None,"next_refresh":None}
    updated=row["updated_at"]
    next_update=datetime.fromtimestamp(updated.timestamp()+settings.stock_refresh_seconds,tz=timezone.utc) if updated else None
    return {"success":updated is not None,"online_members":row["online_members"],
            "offline_members":row["offline_members"],
            "last_updated":updated.isoformat() if updated else None,
            "next_refresh":next_update.isoformat() if next_update else None}
