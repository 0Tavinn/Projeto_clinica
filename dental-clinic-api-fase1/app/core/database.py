"""
Configuração de banco de dados (SQLAlchemy 2.x).

Usa apenas construções compatíveis com MySQL e PostgreSQL (evita tipos e
funções específicas de dialect) para permitir a migração planejada de MySQL
para PostgreSQL sem reescrever os models.
"""
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings

settings = get_settings()


def _engine_kwargs() -> dict:
    kwargs = {"pool_pre_ping": True, "future": True}
    # SQLite (usado em testes) não suporta os parâmetros de pool do MySQL.
    if settings.DATABASE_URL.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        kwargs.update(pool_size=5, max_overflow=10, pool_recycle=1800)
    return kwargs


engine = create_engine(settings.DATABASE_URL, **_engine_kwargs())

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
)


class Base(DeclarativeBase):
    """Base declarativa para todos os models ORM da aplicação."""

    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency do FastAPI: fornece uma sessão de banco por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
