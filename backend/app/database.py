import os
import asyncio
import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

LOCAL_DATABASE_URL = os.getenv("LOCAL_DATABASE_URL", "sqlite+aiosqlite:///./interviewai_dev.db")
USE_REMOTE_DATABASE = os.getenv("USE_REMOTE_DATABASE", "").lower() in {"1", "true", "yes"}
RAW_URL = os.getenv("DATABASE_URL", LOCAL_DATABASE_URL) if USE_REMOTE_DATABASE else LOCAL_DATABASE_URL


def _normalize_database_url(raw_url: str) -> str:
    if raw_url.startswith("postgresql+asyncpg://"):
        return raw_url.split("?")[0] + "?ssl=require"
    if raw_url.startswith("postgresql://"):
        async_url = raw_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return async_url.split("?")[0] + "?ssl=require"
    return raw_url


def _create_engine(database_url: str):
    if database_url.startswith("sqlite"):
        return create_async_engine(database_url, echo=False)
    return create_async_engine(
        database_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
        connect_args={"timeout": 8},
    )


DATABASE_URL = _normalize_database_url(RAW_URL)
print(f"[DB] Configured database at: {DATABASE_URL[:60]}...")

engine = _create_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def init_db():
    global engine, async_session, DATABASE_URL
    try:
        await asyncio.wait_for(_create_tables(), timeout=10)
        await migrate_schema()
    except Exception as exc:
        if DATABASE_URL == LOCAL_DATABASE_URL:
            raise
        print(f"[DB] Remote database unavailable ({exc}). Falling back to local SQLite.")
        await engine.dispose()
        DATABASE_URL = LOCAL_DATABASE_URL
        engine = _create_engine(DATABASE_URL)
        async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        await _create_tables()
        await migrate_schema()


async def _create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"[DB] Tables created/verified using {DATABASE_URL}")

async def migrate_schema():
    """Add missing columns that SQLAlchemy create_all won't add to existing tables."""
    missing_columns = {
        "users": [
            ("token", "VARCHAR(128)"),
        ],
    }
    async with engine.begin() as conn:
        for table, cols in missing_columns.items():
            for col_name, col_type in cols:
                try:
                    await conn.execute(
                        sa.text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}")
                    )
                    print(f"[DB] Added missing column {table}.{col_name}")
                except Exception:
                    pass  # column already exists


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def close_db():
    await engine.dispose()
