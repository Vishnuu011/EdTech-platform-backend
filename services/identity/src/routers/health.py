from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from typing import Dict, Any
from src.health.checks import (
    check_database_connection,
    check_rabbitmq_connection,
    check_redis_connection
)


router=APIRouter(
    prefix="/health",
    tags=["Health"]
)



@router.get(
    "/live",
    status_code=status.HTTP_200_OK
)
async def liveness_check() -> Dict[str, Any]:

    return {
        "status": "OK"
    }



@router.get(
    "/ready",
    status_code=status.HTTP_200_OK
)
async def readiness_all_check() -> Dict[str, Any]:

    database=await check_database_connection()
    redis=await check_redis_connection()
    rabbitmq=await check_rabbitmq_connection()

    dependencies={
        "database": database,
        "redis":redis,
        "rabbitmq": rabbitmq
    }

    ready=all(
        dependency["Status"] == "OK"
        for dependency in dependencies.values()
    )

    response={
        "Status":"ready" if ready else "not_ready",
        "dependencies": dependencies
    }

    return JSONResponse(
        status_code=200 if ready else 503,
        content=response
    )