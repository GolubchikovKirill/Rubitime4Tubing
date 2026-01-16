from __future__ import annotations

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from aiogram.types import Update

from app.config import settings
from app.db import init_db, get_session
from app.services.queue import ensure_base_queues, confirm_by_token
from app.bot.handlers_user import user_router
from app.bot.handlers_operator import operator_router, is_operator
from app.tg_webapp_auth import validate_init_data

bot: Bot | None = None
dp: Dispatcher | None = None

SCANNER_HTML_PATH = Path("webapp/scanner.html")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot, dp

    init_db()
    with get_session() as session:
        ensure_base_queues(session)

    bot = Bot(token=settings.BOT_TOKEN)

    redis = Redis.from_url(settings.REDIS_URL)
    dp = Dispatcher(storage=RedisStorage(redis=redis))  # RedisStorage поддерживается aiogram [web:206]
    dp.include_router(user_router)
    dp.include_router(operator_router)

    await bot.set_webhook(
        url=settings.webhook_url,
        secret_token=settings.WEBHOOK_SECRET or None,
        drop_pending_updates=True,
    )
    yield

    if bot:
        await bot.delete_webhook(drop_pending_updates=True)
        await bot.session.close()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"ok": True}


@app.post("/tg/webhook")
async def tg_webhook(request: Request):
    if settings.WEBHOOK_SECRET:
        secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if secret != settings.WEBHOOK_SECRET:
            raise HTTPException(status_code=401, detail="Invalid secret token")

    data = await request.json()
    update = Update.model_validate(data)
    assert dp is not None and bot is not None
    await dp.feed_update(bot, update)
    return {"ok": True}


@app.get("/webapp/scanner", response_class=HTMLResponse)
async def webapp_scanner():
    if not SCANNER_HTML_PATH.exists():
        raise HTTPException(status_code=500, detail="scanner.html not found")
    return SCANNER_HTML_PATH.read_text(encoding="utf-8")


@app.post("/api/confirm")
async def api_confirm(payload: dict):
    token = (payload.get("token") or "").strip()
    init_data = (payload.get("init_data") or "").strip()

    if not token:
        raise HTTPException(status_code=400, detail="token required")
    if not init_data:
        raise HTTPException(status_code=400, detail="init_data required")

    try:
        data = validate_init_data(init_data, settings.BOT_TOKEN)
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    # user в initData приходит как JSON-строка
    # для простоты вытащим tg user id через примитивный парсинг (лучше: json.loads)
    import json
    user = json.loads(data.get("user", "{}"))
    tg_user_id = int(user.get("id", 0))
    if not tg_user_id or not is_operator(tg_user_id):
        raise HTTPException(status_code=403, detail="Not an operator")

    with get_session() as session:
        t = confirm_by_token(session, token=token)

    if not t:
        raise HTTPException(status_code=404, detail="ticket not found / expired / invalid state")

    return {"ok": True, "ticket_id": t.id, "queue_id": t.queue_id, "status": t.status}
