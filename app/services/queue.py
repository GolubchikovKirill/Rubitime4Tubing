from __future__ import annotations

from datetime import datetime, timedelta, date
from typing import Optional, Sequence
from uuid import uuid4

from sqlmodel import Session, select

from app.models import Queue, TgUser, Ticket, TicketStatus

ACTIVE_STATUSES = (TicketStatus.WAITING, TicketStatus.CALLED, TicketStatus.CONFIRMED)


def ensure_base_queues(session: Session) -> None:
    q1 = session.exec(select(Queue).where(Queue.id == 1)).first()
    q2 = session.exec(select(Queue).where(Queue.id == 2)).first()
    if not q1:
        session.add(Queue(id=1, title="Трасса 1"))
    if not q2:
        session.add(Queue(id=2, title="Трасса 2"))
    session.commit()


def upsert_user(session: Session, tg_user_id: int, tg_chat_id: int, full_name: str) -> TgUser:
    user = session.exec(select(TgUser).where(TgUser.tg_user_id == tg_user_id)).first()
    if user:
        user.tg_chat_id = tg_chat_id
        user.full_name = full_name
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    user = TgUser(tg_user_id=tg_user_id, tg_chat_id=tg_chat_id, full_name=full_name)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_active_ticket(session: Session, user_db_id: int) -> Optional[Ticket]:
    stmt = (
        select(Ticket)
        .where(Ticket.user_id == user_db_id)
        .where(Ticket.status.in_(ACTIVE_STATUSES))
        .order_by(Ticket.created_at.desc())
    )
    return session.exec(stmt).first()


def enqueue(session: Session, queue_id: int, user: TgUser) -> Ticket:
    active = get_active_ticket(session, user.id)
    if active:
        return active
    ticket = Ticket(queue_id=queue_id, user_id=user.id, status=TicketStatus.WAITING)
    session.add(ticket)
    session.commit()
    session.refresh(ticket)
    return ticket


def leave(session: Session, user: TgUser) -> bool:
    active = get_active_ticket(session, user.id)
    if not active:
        return False
    active.status = TicketStatus.CANCELED
    active.canceled_at = datetime.utcnow()
    session.add(active)
    session.commit()
    return True


def position_in_queue(session: Session, ticket: Ticket) -> int:
    stmt = (
        select(Ticket)
        .where(Ticket.queue_id == ticket.queue_id)
        .where(Ticket.status == TicketStatus.WAITING)
        .order_by(Ticket.created_at.asc())
    )
    waiting = list(session.exec(stmt).all())
    for idx, t in enumerate(waiting, start=1):
        if t.id == ticket.id:
            return idx
    return 0


def list_waiting(session: Session, queue_id: int, limit: int = 30) -> Sequence[Ticket]:
    stmt = (
        select(Ticket)
        .where(Ticket.queue_id == queue_id)
        .where(Ticket.status == TicketStatus.WAITING)
        .order_by(Ticket.created_at.asc())
        .limit(limit)
    )
    return session.exec(stmt).all()


def call_next(session: Session, queue_id: int) -> Optional[Ticket]:
    stmt = (
        select(Ticket)
        .where(Ticket.queue_id == queue_id)
        .where(Ticket.status == TicketStatus.WAITING)
        .order_by(Ticket.created_at.asc())
    )
    t = session.exec(stmt).first()
    if not t:
        return None
    t.status = TicketStatus.CALLED
    t.called_at = datetime.utcnow()
    t.confirm_token = uuid4().hex
    t.confirm_token_expires_at = datetime.utcnow() + timedelta(minutes=15)
    session.add(t)
    session.commit()
    session.refresh(t)
    return t


def mark_no_show(session: Session, queue_id: int) -> Optional[Ticket]:
    stmt = (
        select(Ticket)
        .where(Ticket.queue_id == queue_id)
        .where(Ticket.status == TicketStatus.CALLED)
        .order_by(Ticket.called_at.asc())
    )
    t = session.exec(stmt).first()
    if not t:
        return None
    t.status = TicketStatus.NO_SHOW
    t.no_show_at = datetime.utcnow()
    session.add(t)
    session.commit()
    session.refresh(t)
    return t


def confirm_by_token(session: Session, token: str) -> Optional[Ticket]:
    now = datetime.utcnow()
    t = session.exec(select(Ticket).where(Ticket.confirm_token == token)).first()
    if not t:
        return None
    if t.confirm_token_expires_at and t.confirm_token_expires_at < now:
        return None
    if t.status != TicketStatus.CALLED:
        return None
    t.status = TicketStatus.CONFIRMED
    t.confirmed_at = now
    session.add(t)
    session.commit()
    session.refresh(t)
    return t


def serve_confirmed(session: Session, queue_id: int) -> Optional[Ticket]:
    stmt = (
        select(Ticket)
        .where(Ticket.queue_id == queue_id)
        .where(Ticket.status == TicketStatus.CONFIRMED)
        .order_by(Ticket.confirmed_at.asc())
    )
    t = session.exec(stmt).first()
    if not t:
        return None
    t.status = TicketStatus.SERVED
    t.served_at = datetime.utcnow()
    session.add(t)
    session.commit()
    session.refresh(t)
    return t


def day_stats(session: Session, day: date, queue_id: Optional[int] = None) -> dict:
    start = datetime(day.year, day.month, day.day)
    end = start + timedelta(days=1)

    created_stmt = select(Ticket).where(Ticket.created_at >= start).where(Ticket.created_at < end)
    confirmed_stmt = select(Ticket).where(Ticket.confirmed_at >= start).where(Ticket.confirmed_at < end)

    if queue_id is not None:
        created_stmt = created_stmt.where(Ticket.queue_id == queue_id)
        confirmed_stmt = confirmed_stmt.where(Ticket.queue_id == queue_id)

    return {
        "created": len(session.exec(created_stmt).all()),
        "confirmed": len(session.exec(confirmed_stmt).all()),
    }
