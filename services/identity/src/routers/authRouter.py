from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controller.authController import(
    RegisterResponse, 
    RegisterRequest,
    LoginResponse,
    LoginRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    refresh_access_token_identity_service,
    register_identity_services_user,
    login_user_in_identity_service
)

from src.database.session import get_db


router=APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    data: RegisterRequest,
    db: AsyncSession=Depends(
        get_db
    )
) -> RegisterResponse:

    return await register_identity_services_user(
        data=data,
        db=db
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK
)
async def login_user(
    data:LoginRequest,
    db:AsyncSession=Depends(get_db)
) -> LoginResponse:

    return await login_user_in_identity_service(
        data=data,
        db=db
    )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK
)
async def refresh(
    data: RefreshTokenRequest,
    db: AsyncSession=Depends(
        get_db
    )
) -> RefreshTokenResponse:

    return await refresh_access_token_identity_service(
        data=data,
        db=db
    )