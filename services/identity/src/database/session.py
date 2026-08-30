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

    """
    Provide an asynchronous SQLAlchemy database session.

    Creates a database session for the lifetime of a FastAPI request.
    The session is automatically closed when the request finishes.

    If an exception occurs while processing the request, the current
    transaction is rolled back and the exception is propagated to
    FastAPI.

    Yields:
        AsyncSession: An asynchronous SQLAlchemy database session.
    """

    async with SessionLocal() as session:

        try:
            yield session
        except Exception:
            await session.rollback()
            raise    