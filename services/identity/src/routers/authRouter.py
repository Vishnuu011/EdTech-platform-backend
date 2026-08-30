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



oauth2_scheme=OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login"
)



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

    """
    Register a new user account.

    Creates a new user and associated password credential.
    The newly registered account remains pending until the
    email verification process is completed.

    Args:
        data: User registration details.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        RegisterResponse: Newly created user's ID, email,
        and account status.

    Raises:
        HTTPException: 409 Conflict if the email is already registered.
    """

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

    """
    Authenticate a user and initiate OTP-based login verification.

    Validates the user's credentials and, when successful, sends
    a login verification OTP. Access and refresh tokens are issued
    only after the OTP is successfully verified.

    Args:
        request: FastAPI request used by the rate-limiting system.
        data: User login credentials.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        LoginResponse: Indicates that a login verification OTP
        is required.

    Raises:
        HTTPException: 401 Unauthorized for invalid credentials.
        HTTPException: 403 Forbidden when the user account or
            credential is inactive.
        HTTPException: 429 Too Many Requests when the login
            rate limit or OTP cooldown is exceeded.
    """

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

    """
    Verify the login OTP and issue authentication tokens.

    Validates the OTP associated with the user's login attempt.
    When verification succeeds, a new authenticated session is
    created and access and refresh tokens are returned.

    Args:
        request: FastAPI request used by the rate-limiting system.
        data: Login verification request containing the user's
            email and OTP.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        LoginVerifyResponse: Access token, refresh token,
        token type, and access-token expiration time.

    Raises:
        HTTPException: 400 Bad Request for an invalid, expired,
            or locked OTP.
        HTTPException: 401 Unauthorized for an invalid
            verification request.
        HTTPException: 429 Too Many Requests when the OTP
            verification rate limit is exceeded.
    """

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

    """
    Refresh an authenticated session's access token.

    Validates the supplied refresh token and rotates it by issuing
    a new access token and refresh token pair.

    Args:
        data: Request containing the current refresh token.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        RefreshTokenResponse: New access token, rotated refresh
        token, token type, and access-token expiration time.

    Raises:
        HTTPException: 401 Unauthorized when the refresh token
            is invalid, expired, or associated with an inactive
            session.
        HTTPException: 403 Forbidden when the user account is inactive.
    """

    return await refresh_access_token_identity_service(
        data=data,
        db=db
    )




@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT
)
async def logout(
    token:str=Depends(oauth2_scheme),
    db:AsyncSession=Depends(get_db)
) -> None:

    """
    Log out the currently authenticated user.

    Validates the access token and revokes the session associated
    with the token.

    Args:
        token: Bearer access token extracted from the Authorization
            header.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        None: The current session is revoked successfully.

    Raises:
        HTTPException: 401 Unauthorized when the access token
            or associated session is invalid.
    """

    await logout_user_in_identity_service(
        db=db,
        token=token
    )
