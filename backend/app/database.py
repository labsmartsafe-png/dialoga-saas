"""
Configuração de banco de dados com SQLAlchemy.
Suporta SQLite (dev/testes) e PostgreSQL (produção) via variável DATABASE_URL.
"""
import os
import logging
from pathlib import Path
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from .config import settings

logger = logging.getLogger("whatsflow.database")


def _create_engine():
    """Cria engine do SQLAlchemy com base na URL do banco."""
    url = settings.database_url
    if url.startswith("sqlite"):
        # Garante que o diretório do SQLite existe
        db_path = url.replace("sqlite:///", "").replace("sqlite://", "")
        if db_path and db_path != ":memory:":
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


# --------------------------------------------------------------------------- #
# Auto-migração leve (aditiva e idempotente).
# Motivo: o projeto cria tabelas via create_all(), que NUNCA adiciona colunas
# novas a tabelas JÁ existentes. Quando adicionamos uma coluna a um modelo de
# uma tabela que já está no banco (ex.: flows.mode), precisamos garantir que a
# coluna exista também no banco antigo. Esta função verifica e adiciona, sem
# tocar em dados. Só faz ADD COLUMN; nunca dropa/altera coluna existente.
#
# Cada entrada: (tabela, coluna, definicao_sql, default_para_registros_existentes)
# --------------------------------------------------------------------------- #
_ADDITIVE_COLUMNS = [
    ("flows", "mode", "VARCHAR(20)", "guided"),

    # WhatsAppConnection evoluiu em fases (Meta -> Evolution/QR).
    # Em bancos antigos, a tabela whatsapp_connections ja pode existir sem
    # essas colunas; create_all() NAO adiciona coluna nova. Sem esta migracao,
    # qualquer SELECT/INSERT nesta tabela pode gerar 500 em producao.
    ("whatsapp_connections", "flow_id", "INTEGER", None),
    ("whatsapp_connections", "evolution_instance_name", "VARCHAR(150)", None),
    ("whatsapp_connections", "evolution_api_key_enc", "TEXT", None),
    ("whatsapp_connections", "webhook_secret_enc", "TEXT", None),

    # Futuras colunas aditivas em tabelas existentes entram aqui.
    # Ex.: ("users", "is_admin", "BOOLEAN", "0"),
]


def _run_additive_migrations():
    """Adiciona colunas novas em tabelas existentes, de forma segura e idempotente."""
    try:
        inspector = inspect(engine)
        existing_tables = set(inspector.get_table_names())
    except Exception as exc:
        logger.warning("Nao foi possivel inspecionar o banco p/ auto-migracao: %s", exc)
        return

    with engine.begin() as conn:
        for table, column, sql_type, default in _ADDITIVE_COLUMNS:
            if table not in existing_tables:
                continue  # tabela nova -> create_all ja cria com a coluna
            try:
                cols = {c["name"] for c in inspect(engine).get_columns(table)}
            except Exception:
                continue
            if column in cols:
                continue  # coluna ja existe -> nada a fazer
            try:
                # ADD COLUMN (Postgres e SQLite aceitam esta sintaxe basica)
                conn.execute(text(f'ALTER TABLE {table} ADD COLUMN {column} {sql_type}'))
                # Preenche registros existentes com o default
                if default is not None:
                    conn.execute(
                        text(f'UPDATE {table} SET {column} = :d WHERE {column} IS NULL'),
                        {"d": default},
                    )
                logger.info("Auto-migracao: coluna %s.%s adicionada.", table, column)
            except Exception as exc:
                # Nunca deixa a auto-migracao derrubar o app.
                logger.warning("Auto-migracao de %s.%s falhou (seguindo): %s", table, column, exc)


def init_db():
    """Cria todas as tabelas no banco e aplica auto-migrações aditivas."""
    from . import models  # noqa: F401 - importar registra modelos
    Base.metadata.create_all(bind=engine)
    _run_additive_migrations()
