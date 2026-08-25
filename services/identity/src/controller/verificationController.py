from src.helpers.otp import (
    OTP_EXPIRE_SECONDS,
    OTP_LENGTH,
    OTP_RESEND_COOLDOWN_SECOND,
    hash_otp,
    verify_otp,
    generate_otp
)

from src.infrastructure.redis.client import redis_client
from src.infrastructure.messaging.events import publish_email_verification_event

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.enums import UserStatus, VerificationType,VerificationStatus
from src.models.user import User
from src.models.verification import Verification




class SendVerificationRequest(BaseModel):
    email: EmailStr

class SendVerificationResponse(BaseModel):
    message:str

class VerifyVerificationRequest(BaseModel):

    email: EmailStr
    code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )   

class VerifyVerificationResponse(BaseModel):

    message: str
   

        


def get_otp_key(
    verification_type:str,
    destination:str
) -> str:

    return (
        f"identity:otp:"
        f"{verification_type}:"
        f"{destination}"
    )

def get_otp_cooldown_key(
    verification_type:str,
    destination:str
) -> str:

    return (
        f"identity:otp:cooldown:"
        f"{verification_type}:"
        f"{destination}"
    )





async def create_otp(
    user_id:str,
    verification_type: str,
    destination: str
) -> str:

    otp=generate_otp()

    otp_hash=hash_otp(
        otp=otp
    )

    key=get_otp_key(
        verification_type,
        destination
    )

    await redis_client.set(
        key,
        otp_hash,
        ex=OTP_EXPIRE_SECONDS
    )

    await publish_email_verification_event(
        user_id=user_id,
        destination=destination,
        otp=otp
    )

    return otp, otp_hash





async def check_otp(
    verification_type:str,
    destination:str,
    otp:str
) -> bool:

    key=get_otp_key(
        verification_type,
        destination
    )

    stored_hash=await redis_client.get(
        key
    )

    if stored_hash is None:
        return False

    if not verify_otp(
        otp,
        stored_hash
    ):

        return False

    await redis_client.delete(key)

    return True






async def send_verification_Otp(
    data:SendVerificationRequest,
    db:AsyncSession
) -> SendVerificationResponse:

    result=await db.execute(
        select(User).where(
            User.email==data.email
        )
    )

    user=result.scalar_one_or_none()

    if user is None:

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    cooldown_key=get_otp_cooldown_key(
        VerificationType.EMAIL_VERIFICATION.value,
        user.email
    )

    if await redis_client.exists(cooldown_key):

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="please wait before requesting another verification code"
        )

    result=await db.execute(
        select(Verification)
        .where(
            Verification.user_id==user.id,
            Verification.type==VerificationType.EMAIL_VERIFICATION,
            Verification.status==VerificationStatus.PENDING
        )
    )

    pending_verification=result.scalars().all()

    for verification in pending_verification:
        verification.status=VerificationStatus.EXPIRED

    otp, otp_hash=await create_otp(
        user_id=str(user.id),
        verification_type=VerificationType.EMAIL_VERIFICATION.value,
        destination=user.email
    )

    await redis_client.set(
        cooldown_key,
        "1",
        ex=OTP_RESEND_COOLDOWN_SECOND
    )

    verification = Verification(
        user_id=user.id,
        type=VerificationType.EMAIL_VERIFICATION,
        destination=user.email,
        code_hash=otp_hash,
        status=VerificationStatus.PENDING,
        attempts=0,
        max_attempts=5,
        expires_at=datetime.now(timezone.utc) + timedelta(
            seconds=OTP_EXPIRE_SECONDS
        ),
    ) 

    db.add(verification)

    await db.commit()

    return SendVerificationResponse(
        message="verification code sent"
    )






async def verify_verification(
    data: VerifyVerificationRequest,
    db: AsyncSession,
) -> VerifyVerificationResponse:

    
    result = await db.execute(
        select(User).where(
            User.email == data.email
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    result = await db.execute(
        select(Verification)
        .where(
            Verification.user_id == user.id,
            Verification.type
            == VerificationType.EMAIL_VERIFICATION,
            Verification.status
            == VerificationStatus.PENDING,
        )
        .order_by(
            Verification.created_at.desc()
        ).limit(1)
    )

    verification = result.scalar_one_or_none()

    if verification is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending verification found",
        )

    now = datetime.now(timezone.utc)

    if verification.expires_at <= now:

        verification.status = (
            VerificationStatus.EXPIRED
        )

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code expired",
        )

    if verification.attempts >= verification.max_attempts:

        verification.status = (
            VerificationStatus.LOCKED
        )

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many verification attempts",
        )

    valid = await check_otp(
        verification_type=(
            VerificationType.EMAIL_VERIFICATION.value
        ),
        destination=data.email,
        otp=data.code,
    )

    if not valid:

        verification.attempts += 1

        if (
            verification.attempts
            >= verification.max_attempts
        ):
            verification.status = (
                VerificationStatus.LOCKED
            )

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    if valid:
        verification.status = (
            VerificationStatus.VERIFIED
        )
        
        verification.verified_at = now

        user.status=UserStatus.ACTIVE
        
        await db.commit()

    return VerifyVerificationResponse(
        message="Verification successful",
    )

