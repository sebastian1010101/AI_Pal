from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine


def async_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


def create_database(database_url: str) -> tuple[async_sessionmaker[AsyncSession], AsyncEngine]:
    engine = create_async_engine(async_database_url(database_url))
    return async_sessionmaker(engine, expire_on_commit=False), engine
