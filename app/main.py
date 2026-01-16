import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.bot.handlers_operator import operator_router
from app.bot.handlers_user import user_router
from app.db import init_db, get_session
from app.services.queue import ensure_base_queues
from app.config import settings


async def main():
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    init_db()
    with get_session() as session:
        ensure_base_queues(session)

    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(user_router)
    dp.include_router(operator_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
