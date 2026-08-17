import time
from typing import Dict, Any, Optional
from sqlalchemy import text
from src.database.connection import engine
from src.infrastructure.messaging.rabbitmq import rabbitmq
from src.infrastructure.redis.client import redis_client


async def check_database_connection() -> Dict[str, Any]:

    start=time.perf_counter()

    try:
        async with engine.connect() as conn:

            await conn.execute(
                text("SELECT 1")
            )

        latency_ms=(
            time.perf_counter()-start
        )*1000

        return {
            "Status": "OK",
            "latency_ms": round(
                latency_ms, 2
            ),
        }   
    except Exception:
        latency_ms=(
            time.perf_counter()-start
        )*1000 

        return {
            "Status": "ERROR",
            "latency_ms": round(
                latency_ms, 2
            )
        }



async def check_redis_connection() -> Dict[str, Any]:

    start=time.perf_counter()

    try:
        await redis_client.ping()

        latency_ms=(
            time.perf_counter()-start
        )*1000

        return {
            "Status": "OK",
            "latency_ms": round(
                latency_ms, 2
            )
        }
    except Exception:
        latency_ms=(
            time.perf_counter()-start
        )*1000

        return {
            "Status": "ERROR",
            "latency_ms":round(
                latency_ms, 2
            )
        }


async def check_rabbitmq_connection() -> Dict[str, Any]:

    start=time.perf_counter()

    try:
        if rabbitmq.connection is None:
            raise RuntimeError(
                "RabbitMQ is not connected"
            )

        if rabbitmq.connection.is_closed:
            raise RuntimeError(
                "RabbitMQ connection closed"
            )

        latency_ms=(
            time.perf_counter()-start
        )*1000

        return {
            "Status": "OK",
            "latency_ms":round(
                latency_ms, 2
            )
        }
    except Exception:
        latency_ms=(
            time.perf_counter()-start
        )*1000

        return {
            "Status": "ERROR",
            "latency_ms": round(
                latency_ms, 2
            )
        }
    