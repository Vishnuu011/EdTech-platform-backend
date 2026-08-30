from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from pydantic import BaseModel, EmailStr, Field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

import secrets

from src.domain.enums import VerificationStatus, VerificationType
from src.helpers.otp import OTP_EXPIRE_SECONDS, OTP_RESEND_COOLDOWN_SECOND
from src.infrastructure.redis.client import redis_client

from src.models.user import User
from src.models.verification import Verification

from src.helpers.password import hash_password
from src.models.credential import Credential
from src.models.session import Session
from src.domain.enums import SessionStatus
from src.controller.verificationController import (
    create_otp,
    check_otp,
    get_otp_cooldown_key
)





RESET_TOKEN_EXPIRE_SECONDS = 600



def get_reset_token_key(token: str) -> str:

    """
    Generate the Redis key used to store a password reset token.

    Args:
        token: Password reset token.

    Returns:
        str: Redis key associated with the password reset token.
    """

    return f"identity:password-reset:{token}"





async def create_reset_token(user_id:str) -> str:

    """
    Generate and store a temporary password reset token.

    A cryptographically secure random token is generated and stored
    in Redis with the associated user ID. The token automatically
    expires after the configured reset-token lifetime.

    Args:
        user_id: Unique identifier of the user requesting the
            password reset.

    Returns:
        str: Newly generated password reset token.

    Raises:
        Exception: Propagates Redis errors if the token cannot
            be stored.
    """

    token = secrets.token_urlsafe(32)

    key= get_reset_token_key(token=token)

    await redis_client.set(
        key,
        user_id,
        ex=RESET_TOKEN_EXPIRE_SECONDS
    )

    return token




##########################################################################################


class PasswordResetRequest(BaseModel):

    """Request payload for initiating a password reset."""

    email: EmailStr




class PasswordResetResponse(BaseModel):

    """Response returned after requesting a password reset."""

    message: str




class PasswordResetVerifyRequest(BaseModel):

    """Request payload for verifying a password reset OTP."""

    email: EmailStr
    code:str=Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )    



class PasswordResetVerifyResponse(BaseModel):

    """Response returned after successful password reset OTP verification."""

    message: str   
    reset_token: str 



class PasswordResetConfirmRequest(BaseModel):

    """Request payload for setting a new password."""

    reset_token:str
    new_password: str=Field(
        min_length=8,
        max_length=128
    )    


class PasswordResetConfirmResponse(BaseModel):

    """Response returned after successfully resetting a password."""

    message: str


#############################################################################################




async def request_password_reset_identity_service(
    data:PasswordResetRequest,
    db:AsyncSession
) -> PasswordResetResponse:

    """
    Initiate the password reset process for a user.

    The function verifies that the user exists, enforces the OTP
    resend cooldown, expires previous pending password reset
    verifications, generates a new OTP, stores the verification
    record, and publishes the OTP through the verification event
    system.

    Args:
        data: Request containing the user's email address.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        PasswordResetResponse: Confirmation that the password reset
        code was sent.

    Raises:
        HTTPException: 404 Not Found when the user does not exist.
        HTTPException: 429 Too Many Requests when the OTP resend
            cooldown is active.
    """

    result=await db.execute(
        select(User).where(
            User.email==data.email
        )
    )        

    user=result.scalar_one_or_none()

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="If an account exists, a password reset code has been sent"
        )

    cooldown_key=get_otp_cooldown_key(
        VerificationType.PASSWORD_RESET.value,
        user.email
    )

    if await redis_client.exists(cooldown_key):

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="please wait before requesting"
        )

    result=await db.execute(
        select(Verification).where(
            Verification.user_id==user.id,
            Verification.type==VerificationType.PASSWORD_RESET,
            Verification.status==VerificationStatus.PENDING
        )
    )

    pending_verification=result.scalars().all()

    for verification in pending_verification:
        verification.status=VerificationStatus.EXPIRED

    otp, otp_hash=await create_otp(
        user_id=str(user.id),
        verification_type=VerificationType.PASSWORD_RESET.value,
        destination=user.email
    )        

    await redis_client.set(
        cooldown_key,
        "1",
        ex=OTP_RESEND_COOLDOWN_SECOND
    )

    verification=Verification(
        user_id=user.id,
        type=VerificationType.PASSWORD_RESET,
        destination=user.email,
        code_hash=otp_hash,
        status=VerificationStatus.PENDING,
        attempts=0,
        max_attempts=5,
        expires_at=datetime.now(timezone.utc)
        + timedelta(seconds=OTP_EXPIRE_SECONDS)
    )

    db.add(verification)

    await db.commit()

    return PasswordResetResponse(
        message="Password resent code sent"
    )






async def verify_password_reset_identity_service(
    data: PasswordResetVerifyRequest,
    db: AsyncSession,
) -> PasswordResetVerifyResponse:

    """
    Verify a password reset OTP and issue a temporary reset token.

    The function retrieves the latest pending password reset
    verification, validates its expiration and attempt limit,
    verifies the OTP, marks the verification as completed, and
    generates a temporary password reset token.

    Args:
        data: Request containing the user's email address and
            password reset OTP.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        PasswordResetVerifyResponse: Contains a temporary reset token
        that can be used to set a new password.

    Raises:
        HTTPException: 404 Not Found when the user does not exist.
        HTTPException: 400 Bad Request when no pending reset exists,
            the OTP has expired, maximum attempts have been exceeded,
            or the OTP is invalid.
    """


    result = await db.execute(
        select(User).where(
            User.email==data.email
        )
    )

    user=result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = await db.execute(
        select(Verification)
        .where(
            Verification.user_id==user.id,
            Verification.type==VerificationType.PASSWORD_RESET,
            Verification.status==VerificationStatus.PENDING,
        )
        .order_by(
            Verification.created_at.desc()
        )
        .limit(1)
    )

    verification=result.scalar_one_or_none()

    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending password reset found",
        )

    now = datetime.now(timezone.utc)

    if verification.expires_at <= now:

        verification.status=VerificationStatus.EXPIRED

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset code expired",
        )

    if verification.attempts >= verification.max_attempts:

        verification.status = VerificationStatus.LOCKED

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many verification attempts",
        )

    valid = await check_otp(
        verification_type=VerificationType.PASSWORD_RESET.value,
        destination=data.email,
        otp=data.code,
    )

    if not valid:

        verification.attempts += 1

        if verification.attempts >= verification.max_attempts:
            verification.status = VerificationStatus.LOCKED

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset code",
        )

    verification.status=VerificationStatus.VERIFIED
    verification.verified_at=now

    reset_token=await create_reset_token(
        user_id=str(user.id)
    )

    await db.commit()

    return PasswordResetVerifyResponse(
        message="Password reset code verified",
        reset_token=reset_token
    )






async def confirm_password_reset_identity_service(
    data: PasswordResetConfirmRequest,
    db: AsyncSession,
) -> PasswordResetConfirmResponse:

    """
    Set a new password using a valid password reset token.

    The function validates the temporary reset token stored in Redis,
    retrieves the associated user and credential, hashes and updates
    the new password, revokes all active sessions, consumes the reset
    token, and commits the changes to the database.

    Args:
        data: Request containing the temporary reset token and
            the user's new password.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        PasswordResetConfirmResponse: Confirmation that the password
        reset was completed successfully.

    Raises:
        HTTPException: 401 Unauthorized when the reset token is
            invalid or expired.
        HTTPException: 404 Not Found when the associated user or
            credential cannot be found.
    """

    # 1. Find reset token in Redis
    key=get_reset_token_key(
        data.reset_token
    )

    user_id=await redis_client.get(key)

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired reset token",
        )

    # 2. Find user
    result=await db.execute(
        select(User).where(
            User.id==user_id
        )
    )

    user=result.scalar_one_or_none()

    if user is None:
        # Consume the token even if the user no longer exists
        await redis_client.delete(key)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # 3. Find credential
    result = await db.execute(
        select(Credential).where(
            Credential.user_id==user.id
        )
    )

    credential=result.scalar_one_or_none()

    if credential is None:
        await redis_client.delete(key)

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credential not found",
        )

    # 4. Hash new password
    new_password_hash=hash_password(
        data.new_password
    )

    credential.password_hash=new_password_hash
    credential.password_changed_at=datetime.now(
        timezone.utc
    )

    # 5. Revoke all active sessions
    result = await db.execute(
        select(Session).where(
            Session.user_id==user.id,
            Session.status==SessionStatus.ACTIVE,
        )
    )

    active_sessions=result.scalars().all()

    now = datetime.now(timezone.utc)

    for session in active_sessions:
        session.status=SessionStatus.REVOKED
        session.revoked_at=now

    # 6. Consume reset token
    await redis_client.delete(key)

    # 7. Save everything
    await db.commit()

    return PasswordResetConfirmResponse(
        message="Password resent successful",
    )



