from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db

from src.controller.password_reset_controller import (
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

    return await confirm_password_reset_identity_service(
        data=data,
        db=db
    )