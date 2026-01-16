from sqlmodel import SQLModel, Session, create_engine
from app.config import settings

engine = create_engine(settings.DB_URL, pool_pre_ping=True)

def init_db() -> None:
    SQLModel.metadata.create_all(engine)

def get_session() -> Session:
    return Session(engine)
