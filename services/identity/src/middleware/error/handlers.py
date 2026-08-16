import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse


from .exceptions import AppException

logger = logging.getLogger(__name__)


async def app_exception_handler(
    request: Request,
    exe : AppException 
) -> JSONResponse:

    return JSONResponse(
        status_code=exe.status_code,
        content={
            "code": exe.code,
            "message": exe.message,
            "details": exe.details,
            "request_id": None,
        },
    )




async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,    
) -> JSONResponse:

    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Validation error",
            "details": exc.errors(),
            "request_id": None,
        },
    )




async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:

    logger.exception(
        "Unhandled exception occurred",
        extra={
            "path": request.url.path,
            "method": request.method,
        }
    )

    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_SERVER_ERROR",
            "message": "Internal server error",
            "details": None,
            "request_id": None,
        },
    )    


