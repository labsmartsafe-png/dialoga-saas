"""
Configuração de banco de dados com SQLAlchemy.

Suporta SQLite (dev/testes) e PostgreSQL (produção) via variável DATABASE_URL.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from .config import settings


def _create_engine():
    """Cria engine do SQLAlchemy com base na URL do banco."""
    url = settings.database_url
    if url.startswith("sqlite"):
        # Garante que o diretório do SQLite existe
        # Extrai o caminho do arquivo (sqlite:///./data/x.db ou sqlite:////abs/path)
        db_path = url.replace("sqlite:///", "").replace("sqlite://", "")
        if db_path and db_path != ":memory:":
            # Se relativo, resolve em relação ao CWD
            p = Path(db_path)
            if not p.is_absolute():
                p = Path.cwd() / p
            p.parent.mkdir(parents=True, exist_ok=True)
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
    # PostgreSQL - SQLAlchemy 2.0 usa psycopg v3 automaticamente para URLs postgresql+psycopg://
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return create_engine(url, pool_pre_ping=True, echo=False)


engine = _create_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    """Gerador de sessão do banco - dependency do FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Cria todas as tabelas no banco."""
    from . import models  # noqa: F401 - importar registra modelos
    Base.metadata.create_all(bind=engine)
