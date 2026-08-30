from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine
)


from src.config.settings import settings

def create_database_engine() -> AsyncEngine:

    """
    Create and configure the asynchronous SQLAlchemy database engine.

    Creates an async database engine using the configured database URL.
    The engine uses connection health checks before acquiring pooled
    connections to avoid reusing stale connections.

    Returns:
        AsyncEngine: Configured asynchronous SQLAlchemy engine.
    """

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )

engine=create_database_engine()