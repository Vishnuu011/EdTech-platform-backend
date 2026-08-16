from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from .exceptions import AppException
from .handlers import (
    app_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)


def register_exception_handlers(app: FastAPI) -> None:

    app.add_exception_handler(
        AppException,
        app_exception_handler
    )
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler
    )
    app.add_exception_handler(
        Exception,
        unhandled_exception_handler
    )