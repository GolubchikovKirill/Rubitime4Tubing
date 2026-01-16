from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field


class TicketStatus(str, Enum):
    WAITING = "WAITING"
    CALLED = "CALLED"
    CONFIRMED = "CONFIRMED"
    SERVED = "SERVED"
    CANCELED = "CANCELED"
    NO_SHOW = "NO_SHOW"


class Queue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str


class TgUser(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tg_user_id: int = Field(index=True, unique=True)
    tg_chat_id: int
    full_name: str = ""


class Ticket(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    queue_id: int = Field(index=True)
    user_id: int = Field(index=True)

    status: TicketStatus = Field(default=TicketStatus.WAITING, index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    called_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    served_at: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    no_show_at: Optional[datetime] = None

    confirm_token: Optional[str] = Field(default=None, index=True, unique=True)
    confirm_token_expires_at: Optional[datetime] = None
