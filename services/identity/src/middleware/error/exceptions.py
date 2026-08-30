from typing import Any
from fastapi import status



class AppException(Exception):

    def __init__(
        self,
        message: str,
        code: str,
        status_code: int,
        details: Any | None = None
    ) -> None:
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details

        super().__init__(message)


class BadRequestException(AppException):

    def __init__(
        self,
        message: str = "Bad request",
        code: str = "BAD_REQUEST",
        details: Any | None = None
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )        

class UnauthorizedException(AppException):

    def __init__(
        self,
        message: str = "Unauthorized",
        code: str = "UNAUTHORIZED",
        details: Any | None = None
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
    )  

class ForbiddenException(AppException):

    def __init__(
        self,
        message: str = "Forbidden",
        code: str = "FORBIDDEN",
        details: Any | None = None
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details
    )


class NotFoundException(AppException):

    def __init__(
        self,
        message: str = "Not found",
        code: str = "NOT_FOUND",
        details: Any | None = None
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details
    )

class ConflictException(AppException):

    def __init__(
        self,
        message: str = "Conflict",
        code: str = "CONFLICT",
        details: Any | None = None
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_409_CONFLICT,
            details=details
    )


class InternalServerErrorException(AppException):

    def __init__(
        self,
        message: str = "Internal server error",
        code: str = "INTERNAL_SERVER_ERROR",
        details: Any | None = None
    ) -> None:
        super().__init__(
            message=message,
            code=code,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
    )                                      