from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from app.bot.keyboards import user_main_kb
from app.db import get_session
from app.services.queue import upsert_user, enqueue, get_active_ticket, position_in_queue, leave

user_router = Router(name="user")


@user_router.message(CommandStart())
async def start(message: Message):
    await message.answer("Живая очередь: выберите действие.", reply_markup=user_main_kb())


@user_router.callback_query(F.data.startswith("u:enq:"))
async def user_enqueue(cb: CallbackQuery):
    queue_id = int(cb.data.split(":")[2])
    with get_session() as session:
        user = upsert_user(session, cb.from_user.id, cb.message.chat.id, cb.from_user.full_name or "")
        ticket = enqueue(session, queue_id=queue_id, user=user)

        if ticket.status.name == "WAITING":
            pos = position_in_queue(session, ticket)
            await cb.message.answer(f"Вы в очереди на Трасса {queue_id}. Ваш номер в ожидании: {pos}.")
        else:
            await cb.message.answer(f"У вас уже есть активная запись (статус: {ticket.status}, Трасса {ticket.queue_id}).")

    await cb.answer()


@user_router.callback_query(F.data == "u:pos")
async def user_position(cb: CallbackQuery):
    with get_session() as session:
        user = upsert_user(session, cb.from_user.id, cb.message.chat.id, cb.from_user.full_name or "")
        ticket = get_active_ticket(session, user.id)
        if not ticket:
            await cb.message.answer("У вас нет активной записи.")
            await cb.answer()
            return

        if ticket.status.name == "WAITING":
            pos = position_in_queue(session, ticket)
            await cb.message.answer(f"Вы ждёте на Трасса {ticket.queue_id}. Позиция: {pos}.")
        else:
            await cb.message.answer(f"Ваш статус: {ticket.status} (Трасса {ticket.queue_id}).")

    await cb.answer()


@user_router.callback_query(F.data == "u:leave")
async def user_leave(cb: CallbackQuery):
    with get_session() as session:
        user = upsert_user(session, cb.from_user.id, cb.message.chat.id, cb.from_user.full_name or "")
        ok = leave(session, user)
    await cb.message.answer("Вы вышли из очереди." if ok else "У вас нет активной записи.")
    await cb.answer()
