from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models.base import Base

database_url = settings.DATABASE_URL
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

engine_kwargs: dict = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "future": True,
}
if database_url.startswith("sqlite"):
    engine_kwargs.pop("pool_size", None)
    engine_kwargs.pop("max_overflow", None)
    engine_kwargs["connect_args"] = {"check_same_thread": False, "timeout": 15}
elif database_url.startswith("mssql"):
    engine_kwargs["connect_args"] = {"timeout": 30}
    engine_kwargs["fast_executemany"] = True

engine = create_engine(database_url, **engine_kwargs)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    future=True,
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_sqlite_schema() -> None:
    if not database_url.startswith("sqlite"):
        return

    with engine.begin() as connection:
        customer_columns = {
            row[1]
            for row in connection.exec_driver_sql("PRAGMA table_info(customers)").fetchall()
        }
        customer_additions = {
            "birthday": "DATE",
            "anniversary": "DATE",
            "special_event_date": "DATE",
            "special_event_name": "VARCHAR(120)",
        }
        for column, column_type in customer_additions.items():
            if column not in customer_columns:
                connection.execute(text(f"ALTER TABLE customers ADD COLUMN {column} {column_type}"))
