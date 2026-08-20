"""SQLAlchemy engine and transaction helpers."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings
from app.db.models import Base

logger = logging.getLogger(__name__)


def create_database_engine(database_url: str | None = None) -> Engine:
    url = database_url or settings.sqlalchemy_url()
    parsed = make_url(url)
    if parsed.drivername.startswith("sqlite") and parsed.database not in {None, ":memory:"}:
        Path(parsed.database).parent.mkdir(parents=True, exist_ok=True)
    database_engine = create_engine(url, pool_pre_ping=True)

    if parsed.drivername.startswith("sqlite"):

        @event.listens_for(database_engine, "connect")
        def enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return database_engine


engine = create_database_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def initialize_database(database_engine: Engine = engine) -> None:
    settings.validate()
    Base.metadata.create_all(database_engine)
    user_columns = {column["name"] for column in inspect(database_engine).get_columns("users")}
    if "is_demo" not in user_columns:
        with database_engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE users ADD COLUMN is_demo BOOLEAN NOT NULL DEFAULT FALSE")
            )
    logger.info("Database schema is ready")


@contextmanager
def session_scope(session_factory=SessionLocal) -> Iterator[Session]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        logger.exception("Database transaction rolled back")
        raise
    finally:
        session.close()
