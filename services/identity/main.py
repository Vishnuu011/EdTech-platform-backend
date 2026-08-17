from src.config.settings import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time
from src.routers import health
from src.infrastructure.messaging.rabbitmq import rabbitmq
from src.database.connection import engine
from src.infrastructure.redis.client import redis_client
from sqlalchemy import text
from src.middleware.error import (
    register_exception_handlers
)
from shared.logging.logger import configure_logger, get_logger

from contextlib import asynccontextmanager
import sys
from pathlib import Path


configure_logger(
    service_name="identity-service",
    log_level="INFO"
)

logger=get_logger(__name__)

async def check_database_connection():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        return result.scalar() == 1


async def check_redis_connection():
    return await redis_client.ping()   


async def check_rabbitmq_connection():
    if not rabbitmq.is_connected:
        await rabbitmq.connect()

    return rabbitmq.is_connected 


@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info(
        "Starting identity-service..."
    )

    try:
        # Database
        await check_database_connection()
        logger.info(
            "PostgreSQL connected"
        )

        # Redis
        await check_redis_connection()
        logger.info(
            "Redis connected"
        )

        # RabbitMQ
        await rabbitmq.connect()
        logger.info("RabbitMQ connected")

        logger.info(
            "Identity-service started successfully"
        )

        yield

    except Exception:
        logger.exception(
            "Failed to start identity-service"
        )
        raise

    finally:
        logger.info(
            "Shutting down identity-service"
        )

        await rabbitmq.close()
        await redis_client.aclose()
        await engine.dispose()

        logger.info(
            "Identity-service shutdown complete"
        )

    



app=FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
    description="Identity Service for EdTech Platform",
    version=settings.APP_VERSION,
)



register_exception_handlers(
    app=app
)



@app.middleware("http")
async def add_process_time_header(
    request, call_next
):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response



app.include_router(health.router)




if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

