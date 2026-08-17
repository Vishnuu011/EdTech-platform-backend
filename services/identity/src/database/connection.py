from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine
)


from src.config.settings import settings

def create_database_engine() -> AsyncEngine:

    return create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )

engine=create_database_engine()