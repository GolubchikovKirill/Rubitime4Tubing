from datetime import date
from io import BytesIO

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile

import qrcode

from app.bot.keyboards import operator_main_kb
from app.config import settings
from app.db import get_session
from app.models import TgUser
from app.services.queue import call_next, list_waiting, mark_no_show, serve_confirmed, day_stats

operator_router = Router(name="operator")


def is_operator(tg_user_id: int) -> bool:
    return tg_user_id in settings.operator_id_set()


def make_qr_png_bytes(payload: str) -> bytes:
    img = qrcode.make(payload)
    bio = BytesIO()
    img.save(bio, format="PNG")
    return bio.getvalue()


@operator_router.message(Command("op"))
async def op_menu(message: Message):
    if not is_operator(message.from_user.id):
        await message.answer("Нет доступа.")
        return
    await message.answer("Операторское меню:", reply_markup=operator_main_kb())


@operator_router.message(Command("stats"))
async def op_stats(message: Message):
    if not is_operator(message.from_user.id):
        await message.answer("Нет доступа.")
        return
    with get_session() as session:
        s1 = day_stats(session, day=date.today(), queue_id=1)
        s2 = day_stats(session, day=date.today(), queue_id=2)
        total = day_stats(session, day=date.today(), queue_id=None)
    await message.answer(
        "Статистика за сегодня:\n"
        f"Трасса 1: встали={s1['created']}, подтвердили(QR)={s1['confirmed']}\n"
        f"Трасса 2: встали={s2['created']}, подтвердили(QR)={s2['confirmed']}\n"
        f"Итого: встали={total['created']}, подтвердили(QR)={total['confirmed']}"
    )


@operator_router.callback_query(F.data.startswith("op:"))
async def op_actions(cb: CallbackQuery):
    if not is_operator(cb.from_user.id):
        await cb.answer("Нет доступа", show_alert=True)
        return

    try:
        _, action, queue_id_s = cb.data.split(":")
        queue_id = int(queue_id_s)
    except Exception:
        await cb.answer("Некорректная кнопка", show_alert=True)
        return

    if action == "list":
        with get_session() as session:
            tickets = list_waiting(session, queue_id=queue_id, limit=30)
            if not tickets:
                await cb.message.answer(f"Трасса {queue_id}: очередь пустая.")
                await cb.answer()
                return
            lines = []
            for i, t in enumerate(tickets, start=1):
                u = session.get(TgUser, t.user_id)
                name = (u.full_name if u else "unknown").strip() or "Без имени"
                lines.append(f"{i}. #{t.id} — {name}")
        await cb.message.answer(f"Трасса {queue_id}: первые {len(lines)} ожидающих:\n" + "\n".join(lines))
        await cb.answer()
        return

    if action == "next":
        with get_session() as session:
            t = call_next(session, queue_id=queue_id)
            if not t:
                await cb.message.answer(f"Трасса {queue_id}: очередь пустая.")
                await cb.answer()
                return
            user = session.get(TgUser, t.user_id)

        await cb.message.answer(f"Трасса {queue_id}: вызван ticket #{t.id}.")

        if user and t.confirm_token:
            payload = f"q:{t.id}:{t.confirm_token}"
            png = make_qr_png_bytes(payload)
            photo = BufferedInputFile(png, filename=f"ticket_{t.id}.png")
            await cb.bot.send_photo(
                chat_id=user.tg_chat_id,
                photo=photo,
                caption=f"Вас вызывают на Трасса {queue_id}! Покажите QR оператору для подтверждения.",
            )

        await cb.answer()
        return

    if action == "noshow":
        with get_session() as session:
            t = mark_no_show(session, queue_id=queue_id)
        await cb.message.answer(
            f"Трасса {queue_id}: отмечен NO_SHOW для ticket #{t.id}." if t else f"Трасса {queue_id}: нет вызванного (CALLED)."
        )
        await cb.answer()
        return

    if action == "serve":
        with get_session() as session:
            served = serve_confirmed(session, queue_id=queue_id)
        await cb.message.answer(
            f"Трасса {queue_id}: завершён ticket #{served.id}." if served else f"Трасса {queue_id}: нет CONFIRMED для завершения."
        )
        await cb.answer()
        return

    await cb.answer("Неизвестное действие", show_alert=True)
