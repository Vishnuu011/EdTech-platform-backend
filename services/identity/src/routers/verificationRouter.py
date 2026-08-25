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


router=APIRouter()


@router.post(
    "/send",
    response_model=SendVerificationResponse,
    status_code=status.HTTP_202_ACCEPTED
)
async def send_verification(
    data:SendVerificationRequest,
    db:AsyncSession=Depends(get_db)
) -> SendVerificationResponse:

    return await send_verification_Otp(
        data=data,
        db=db
    )


@router.post(
    "/verify",
    response_model=VerifyVerificationResponse,
    status_code=status.HTTP_200_OK
)
async def verify_otp(
    data:VerifyVerificationRequest,
    db:AsyncSession=Depends(get_db)
) -> VerifyVerificationResponse:

    return await verify_verification(
        data=data,
        db=db
    )
