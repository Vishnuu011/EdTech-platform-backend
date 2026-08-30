import time
from typing import Dict, Any, Optional
from sqlalchemy import text
from src.database.connection import engine
from src.infrastructure.messaging.rabbitmq import rabbitmq
from src.infrastructure.redis.client import redis_client


async def check_database_connection() -> Dict[str, Any]:

    """
    Check database connectivity and measure query latency.

    Opens an asynchronous database connection and executes a simple
    ``SELECT 1`` query to verify that the database is reachable and
    responding.

    Returns:
        dict[str, Any]: Health-check result containing the connection
        status and measured latency in milliseconds.
    """

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
            "status": "OK",
            "latency_ms": round(
                latency_ms, 2
            ),
        }   
    except Exception:
        latency_ms=(
            time.perf_counter()-start
        )*1000 

        return {
            "status": "ERROR",
            "latency_ms": round(
                latency_ms, 2
            )
        }



async def check_redis_connection() -> Dict[str, Any]:

    """
    Check Redis connectivity and measure ping latency.

    Sends a ``PING`` command to Redis to verify that the Redis
    service is reachable and responding.

    Returns:
        dict[str, Any]: Health-check result containing the Redis
        status and measured latency in milliseconds.
    """

    start=time.perf_counter()

    try:
        await redis_client.ping()

        latency_ms=(
            time.perf_counter()-start
        )*1000

        return {
            "status": "OK",
            "latency_ms": round(
                latency_ms, 2
            )
        }
    except Exception:
        latency_ms=(
            time.perf_counter()-start
        )*1000

        return {
            "status": "ERROR",
            "latency_ms":round(
                latency_ms, 2
            )
        }


async def check_rabbitmq_connection() -> Dict[str, Any]:

    """
    Check whether the RabbitMQ connection is currently available.

    This check verifies that a RabbitMQ connection exists and has
    not been closed. It does not publish a message or perform a
    broker round-trip.

    Returns:
        dict[str, Any]: Health-check result containing the RabbitMQ
        connection status.

    Note:
        The reported latency represents the local connection-state
        check rather than actual RabbitMQ network latency.
    """

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
            "status": "OK",
            "latency_ms":round(
                latency_ms, 2
            )
        }
    except Exception:
        latency_ms=(
            time.perf_counter()-start
        )*1000

        return {
            "status": "ERROR",
            "latency_ms": round(
                latency_ms, 2
            )
        }
    