import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI,Response
from .settings import settings
from .stock import StockStore,sync_loop,stock_payload
from .bot import SaphireBot
from .logging_setup import configure_logging

configure_logging()
store=StockStore()

@asynccontextmanager
async def lifespan(app):
    await store.connect()
    stop=asyncio.Event()
    tasks=[]
    bot=None
    if settings.enable_stock_sync:
        tasks.append(asyncio.create_task(sync_loop(store,stop)))
    if settings.enable_discord_bot:
        if not settings.discord_token:
            raise RuntimeError("DISCORD_TOKEN must be set")
        bot=SaphireBot(store)
        tasks.append(asyncio.create_task(bot.start(settings.discord_token)))
    try:
        yield
    finally:
        stop.set()
        if bot: await bot.close()
        for task in tasks: task.cancel()
        await asyncio.gather(*tasks,return_exceptions=True)
        await store.close()

app=FastAPI(title="Saphire V4 Public API",lifespan=lifespan)
@app.get("/v4/health")
@app.get("/v4/")
@app.get("/v4")
@app.get("/v4/api")
@app.get("/v4/api/health")
async def health():
    return {"success":True,"service":"saphire-v4"}
@app.get("/v4/stock/members")
@app.get("/v4/api/stock/members")
@app.get("/v4/api/members/stock")
async def stock(response:Response):
    response.headers["Cache-Control"]="public, max-age=10"
    payload=stock_payload(await store.get())
    if not payload["success"]: response.status_code=503
    return payload
@app.get("/api/v2/stock")
async def stock_alias(response:Response):
    return await stock(response)
