from fastapi import APIRouter, status, Depends
from src.database.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from src.controller.verificationController import (
    send_verification_Otp, 
    SendVerificationResponse, 
    SendVerificationRequest,
    VerifyVerificationResponse,
    VerifyVerificationRequest,
    verify_verification

)

from src.middleware.rate_limit.decorator import rate_limit





router=APIRouter()





@router.post(
    "/send",
    response_model=SendVerificationResponse,
    status_code=status.HTTP_202_ACCEPTED
)
@rate_limit(
    limit=2,
    window_seconds=300,
    key_prefix="verification-send",
    key_fields=["data.email"]
)
async def send_verification(
    data:SendVerificationRequest,
    db:AsyncSession=Depends(get_db)
) -> SendVerificationResponse:

    """
    Send an email verification OTP to the user.

    Generates a new verification OTP, stores the verification
    information, and publishes the OTP through the verification
    event system. A resend cooldown is enforced to prevent abuse.

    Args:
        data: Request containing the user's email address.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        SendVerificationResponse: Confirmation that the verification
        code was sent successfully.

    Raises:
        HTTPException: 404 Not Found if the user does not exist.
        HTTPException: 429 Too Many Requests if the verification
            OTP resend rate limit or cooldown is exceeded.
    """

    return await send_verification_Otp(
        data=data,
        db=db
    )





@router.post(
    "/verify",
    response_model=VerifyVerificationResponse,
    status_code=status.HTTP_200_OK
)
@rate_limit(
    limit=5,
    window_seconds=300,
    key_prefix="verification-verify"
)
async def verify_otp(
    data:VerifyVerificationRequest,
    db:AsyncSession=Depends(get_db)
) -> VerifyVerificationResponse:

    """
    Verify the user's email verification OTP.

    Validates the submitted OTP against the latest pending email
    verification record. When verification succeeds, the user's
    account is activated.

    Args:
        data: Request containing the user's email address and
            six-digit verification code.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        VerifyVerificationResponse: Confirmation that the email
        verification was successful.

    Raises:
        HTTPException: 404 Not Found if the user does not exist.
        HTTPException: 400 Bad Request if the verification code
            is invalid, expired, locked, or no pending verification
            exists.
        HTTPException: 429 Too Many Requests if the OTP verification
            rate limit is exceeded.
    """

    return await verify_verification(
        data=data,
        db=db
    )
