from src.config.settings import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time

from src.routers import health
from src.infrastructure.messaging.rabbitmq import rabbitmq
from src.database.connection import engine
from src.infrastructure.redis.client import redis_client
from sqlalchemy import text

from src.middleware.correlation.middlerware import CorrelationIDMiddleware
from src.middleware.security.headers import SecurityHeadersMiddleware
from shared.observability.middleware import ObservabilityMiddleware
from src.middleware.error import (
    register_exception_handlers
)
from shared.logging.logger import (
    configure_logger, 
    get_logger
)

from contextlib import asynccontextmanager


from src.routers import (
    authRouter, 
    verificationRouter, 
    passwordResetRouter, 
    userRouter, 
    sessionRouter
)


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

cors_origins=[
    origin.strip()
    for origin in settings.CORS_ORIGINS.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=[
        "GET", "POST", 
        "PUT", "PATCH", 
        "DELETE", "OPTIONS"
    ],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "X-Correlation-ID"
    ]
)



app.add_middleware(
    SecurityHeadersMiddleware
)

app.add_middleware(
    ObservabilityMiddleware
)


app.add_middleware(
    CorrelationIDMiddleware
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


app.include_router(
    authRouter.router,
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


app.include_router(
    verificationRouter.router,
    prefix="/api/v1/verification",
    tags=["Verification"]
)


app.include_router(
    passwordResetRouter.router,
    prefix="/api/v1/password-reset",
    tags=["Password Reset"]
)


app.include_router(
    userRouter.router,
    prefix="/api/v1/users",
    tags=["Users"]
)


app.include_router(
    sessionRouter.router,
    prefix="/api/v1/sessions",
    tags=["Sessions"]
)


@app.get("/", status_code=200)
async def root():
    return {
        "message": "🤗 Welcome to the Identity Service for EdTech Platform Backend API 🤗",
        "version": settings.APP_VERSION,
        "status": "⚙️ running......",
        "documentation": "🌐 /docs",
        "health_check": "🌐 /health/ready or /health/live",

    }



if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

