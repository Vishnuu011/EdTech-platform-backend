from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db

from src.controller.passwordResetController import (
    PasswordResetResponse,
    PasswordResetVerifyResponse,
    PasswordResetVerifyRequest,
    PasswordResetRequest,
    PasswordResetConfirmResponse,
    PasswordResetConfirmRequest,
    request_password_reset_identity_service,
    verify_password_reset_identity_service,
    confirm_password_reset_identity_service
)

from src.middleware.rate_limit.decorator import rate_limit






router=APIRouter()






@router.post(
    "/request",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_202_ACCEPTED
)
@rate_limit(
    limit=2,
    window_seconds=600,
    key_prefix="password-reset",
    key_fields=["data.email"]
)
async def password_reset_request(
    data:PasswordResetRequest,
    db:AsyncSession=Depends(get_db)
) -> PasswordResetResponse:

    """
    Initiate the password reset process for a user.

    Validates the user's email, applies password reset rate limiting,
    generates a password reset OTP, and sends the verification code
    through the verification event system.

    Args:
        data: Request containing the user's email address.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        PasswordResetResponse: Confirmation that the password reset
        code has been sent.

    Raises:
        HTTPException: 404 Not Found when the user does not exist.
        HTTPException: 429 Too Many Requests when the password reset
            rate limit or OTP cooldown is exceeded.
    """

    return await request_password_reset_identity_service(
        data=data,
        db=db
    )






@router.post(
    "/verify",
    response_model=PasswordResetVerifyResponse,
    status_code=status.HTTP_200_OK,
)
async def password_reset_verify(
    data: PasswordResetVerifyRequest,
    db: AsyncSession = Depends(get_db),
) -> PasswordResetVerifyResponse:

    """
    Verify the password reset OTP.

    Validates the submitted password reset code and, when successful,
    issues a temporary password reset token that can be used to
    set a new password.

    Args:
        data: Request containing the user's email address and
            password reset OTP.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        PasswordResetVerifyResponse: Contains a temporary reset token
        for completing the password reset process.

    Raises:
        HTTPException: 404 Not Found when the user does not exist.
        HTTPException: 400 Bad Request when the verification code
            is invalid, expired, locked, or no pending verification
            exists.
    """

    return await verify_password_reset_identity_service(
        data=data,
        db=db,
    )







@router.post(
    "/confirm",
    response_model=PasswordResetConfirmResponse,
    status_code=status.HTTP_200_OK
)
async def password_reset_confirm(
    data:PasswordResetConfirmRequest,
    db:AsyncSession=Depends(get_db)
) -> PasswordResetConfirmResponse:

    """
    Confirm a password reset and set a new password.

    Validates the temporary password reset token, updates the user's
    password, revokes all active sessions, and consumes the reset
    token so that it cannot be reused.

    Args:
        data: Request containing the temporary reset token and
            the new password.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        PasswordResetConfirmResponse: Confirmation that the password
        was successfully reset.

    Raises:
        HTTPException: 401 Unauthorized when the reset token is
            invalid or expired.
        HTTPException: 404 Not Found when the associated user or
            credential cannot be found.
    """

    return await confirm_password_reset_identity_service(
        data=data,
        db=db
    )