from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any
from src.health.checks import (
    check_database_connection,
    check_rabbitmq_connection,
    check_redis_connection
)
from shared.logging.logger import configure_logger, get_logger

configure_logger(
    service_name="identity-service",
    log_level="INFO"
)

logger=get_logger(__name__)


router=APIRouter(
    prefix="/health",
    tags=["Health"]
)



@router.get(
    "/live",
    status_code=status.HTTP_200_OK
)
async def liveness_check(request: Request) -> Dict[str, Any]:

    """
    Check whether the identity service process is alive.

    This endpoint is intended for container orchestration and load
    balancer liveness probes. It does not check external dependencies
    such as the database, Redis, or RabbitMQ.

    Args:
        request: Incoming FastAPI request.

    Returns:
        Dict[str, Any]: A response indicating that the service is alive.
    """


    return {
        "status": "OK"
    }






@router.get(
    "/ready",
    status_code=status.HTTP_200_OK
)
async def readiness_all_check() -> Dict[str, Any]:

    """
    Check whether the identity service is ready to receive traffic.

    The endpoint verifies connectivity to all required infrastructure
    dependencies, including PostgreSQL, Redis, and RabbitMQ. The
    service is considered ready only when all dependencies are healthy.

    Returns:
        Dict[str, Any]: Readiness status and the health status of
        each required dependency.

    Notes:
        Returns HTTP 200 when all dependencies are healthy and
        HTTP 503 Service Unavailable when one or more dependencies
        are unavailable.
    """

    database=await check_database_connection()
    redis=await check_redis_connection()
    rabbitmq=await check_rabbitmq_connection()

    dependencies={
        "database": database,
        "redis":redis,
        "rabbitmq": rabbitmq
    }

    ready=all(
        dependency["status"] == "OK"
        for dependency in dependencies.values()
    )

    response={
        "status":"ready" if ready else "not_ready",
        "dependencies": dependencies
    }

    return JSONResponse(
        status_code=200 if ready else 503,
        content=response
    )