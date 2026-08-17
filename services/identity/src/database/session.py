from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker
)

from src.config.settings import settings
from src.database.connection import engine

SessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:

    async with SessionLocal() as session:

        try:
            yield session
        except Exception:
            await session.rollback()
            raise    