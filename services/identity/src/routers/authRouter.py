from fastapi import (
    APIRouter, 
    Depends, 
    Header, 
    status, 
    HTTPException, 
    Request
)

from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordBearer

from src.controller.authController import(
    RegisterResponse, 
    RegisterRequest,
    LoginResponse,
    LoginRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    LoginVerifyRequest,
    LoginVerifyResponse,
    refresh_access_token_identity_service,
    register_identity_services_user,
    verify_login_otp_identity_service,
    login_user_in_identity_service,
    logout_user_in_identity_service
)

from src.database.session import get_db
from src.middleware.rate_limit.decorator import rate_limit




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
@rate_limit(
    limit=1,
    window_seconds=60,
    key_prefix="login"
)
async def login_user(
    request: Request,
    data:LoginRequest,
    db:AsyncSession=Depends(get_db)
) -> LoginResponse:

    return await login_user_in_identity_service(
        data=data,
        db=db
    )



@router.post(
    "/login/verify",
    response_model=LoginVerifyResponse,
    status_code=status.HTTP_200_OK
)
@rate_limit(
    limit=5,
    window_seconds=300,
    key_prefix="login-verify",
    key_fields=["data.email"]
)
async def verify_login_otp(
    request: Request,
    data:LoginVerifyRequest,
    db:AsyncSession=Depends(get_db)
) -> LoginVerifyResponse:

    return await verify_login_otp_identity_service(
        db=db,
        data=data
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



oauth2_scheme=OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT
)
async def logout(
    token:str=Depends(oauth2_scheme),
    db:AsyncSession=Depends(get_db)
) -> None:


    await logout_user_in_identity_service(
        db=db,
        token=token
    )
