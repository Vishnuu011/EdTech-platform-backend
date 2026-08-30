from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from pydantic import (
    BaseModel,
    EmailStr,
    Field
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import (
    CredentialStatus, 
    UserStatus, 
    SessionStatus,  
    VerificationStatus, 
    VerificationType
)
from src.helpers.password import hash_password
from src.models.credential import Credential
from src.models.verification import Verification
from src.models.user import User
from src.models.session import Session

from src.helpers.jwt import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token
)

from src.helpers.otp import (
    OTP_EXPIRE_SECONDS,
    OTP_RESEND_COOLDOWN_SECOND
)

from src.controller.verificationController import (
    create_otp,
    check_otp,
    get_otp_cooldown_key
)

from src.helpers.token import hash_token, verify_token_hash
from src.helpers.password import verify_password

from src.infrastructure.redis.client import redis_client





##########################################################################


class RegisterRequest(BaseModel):

    """Request payload for registering a new user."""

    email:EmailStr
    password:str=Field(
        min_length=8, 
        max_length=128
    )
    display_name:str=Field(
        min_length=1,
        max_length=100
    )
    phone:str | None=Field(
        default=None,
        min_length=7,
        max_length=20
    )


class RegisterResponse(BaseModel):

    """Response returned after successful user registration."""

    user_id:str
    email:EmailStr
    status:UserStatus


class LoginRequest(BaseModel):

    """Request payload containing user login credentials."""

    email: EmailStr
    password:str=Field(
        min_length=8, 
        max_length=128
    )


class LoginVerifyRequest(BaseModel):

    """Request payload for verifying a login OTP."""

    email:EmailStr
    code:str=Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$"
    )


class LoginVerifyResponse(BaseModel):

    """Response containing authentication tokens after OTP verification."""

    access_token:str
    refresh_token:str
    token_type:str
    expires_in:int    



class LoginResponse(BaseModel):

    """Response returned when login requires OTP verification."""

    message:str
    otp_required:bool   




class RefreshTokenRequest(BaseModel):

    """Request payload containing a refresh token."""

    refresh_token: str



class RefreshTokenResponse(BaseModel):

    """Response containing rotated authentication tokens."""

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int    

##############################################################################



async def register_identity_services_user(
    db: AsyncSession,
    data: RegisterRequest    
) -> RegisterResponse:

    """
    Register a new user and create their password credential.

    The function checks whether the email is already registered, hashes
    the user's password, creates the user with a pending status, and
    creates an active password credential associated with the user.

    Args:
        db: Asynchronous SQLAlchemy database session.
        data: User registration data including email, password,
            display name, and optional phone number.

    Returns:
        RegisterResponse: The newly created user's ID, email, and
        current account status.

    Raises:
        HTTPException: 409 Conflict if the email is already registered
            or a unique-constraint conflict occurs.
    """

    email=str(
        data.email
    ).lower().strip()

    result=await db.execute(
        select(User).
        where(
          User.email==email
        )
    )

    Euser=result.scalar_one_or_none()
    conflict=status.HTTP_409_CONFLICT
    if Euser is not None:
        
        raise HTTPException(
            status_code=conflict,
            detail="alredy register"
        )

    password_hash=hash_password(
        password=data.password
    )
    displayname=data.display_name.strip()
    user=User(
       email=email,
       phone=data.phone,
       display_name=displayname,
       status=UserStatus.PENDING
    )

    db.add(user)

    try:
        await db.flush()

        credential=Credential(
            user_id=user.id,
            password_hash=password_hash,
            status=CredentialStatus.ACTIVE,
            password_changed_at=datetime.now(
                timezone.utc
            )
        )

        db.add(credential)

        await db.commit()
        
    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=conflict,
            detail="User already exist"
        )

    return RegisterResponse(
        user_id=str(user.id),
        email=user.email,
        status=user.status
    )






async def login_user_in_identity_service(
    db: AsyncSession,
    data: LoginRequest,
) -> LoginResponse:

    """
    Authenticate a user and initiate OTP-based login verification.

    The function validates the user's email and password, checks that
    the user account and credential are active, enforces the OTP resend
    cooldown using Redis, expires previous pending login OTPs, and
    creates a new login OTP verification record.

    Args:
        db: Asynchronous SQLAlchemy database session.
        data: Login credentials containing the user's email and password.

    Returns:
        LoginResponse: Indicates that login verification is required
        and that a login OTP has been sent.

    Raises:
        HTTPException: 401 Unauthorized when the email or password is
            invalid.
        HTTPException: 403 Forbidden when the user account or credential
            is inactive.
        HTTPException: 429 Too Many Requests when the OTP resend
            cooldown is active.
    """
    

    email = str(
        data.email
    ).lower().strip()


    # 1. Find user
    result = await db.execute(
        select(User).where(
            User.email == email
        )
    )

    user = result.scalar_one_or_none()

    unauth = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid email or password"

    if user is None:

        raise HTTPException(
            status_code=unauth,
            detail=detail,
        )

    # 2. User must be active
    if user.status!=UserStatus.ACTIVE:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )

    # 3. Find credential
    result = await db.execute(
        select(Credential).where(
            Credential.user_id == user.id
        )
    )

    credential = result.scalar_one_or_none()

    if credential is None:

        raise HTTPException(
            status_code=unauth,
            detail=detail,
        )

  
    if credential.status!=CredentialStatus.ACTIVE:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Credential is not active",
        )


    if not verify_password(
        data.password,
        credential.password_hash,
    ):

        raise HTTPException(
            status_code=unauth,
            detail=detail,
        )

    cooldown_key=get_otp_cooldown_key(
        VerificationType.LOGIN_OTP.value,
        user.email
    )

    if await redis_client.exists(cooldown_key):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting another login code"
        )

    await redis_client.set(
        cooldown_key,
        "1",
        ex=OTP_RESEND_COOLDOWN_SECOND
    )

    result = await db.execute(
        select(Verification).where(
            Verification.user_id==user.id,
            Verification.type==VerificationType.LOGIN_OTP,
            Verification.status==VerificationStatus.PENDING,
        )
    )

    pending_verifications=result.scalars().all()

    for verification in pending_verifications:

        verification.status = (
            VerificationStatus.EXPIRED
        )

    # 7. Generate LOGIN OTP
    otp, otp_hash = await create_otp(
        user_id=str(user.id),
        verification_type=VerificationType.LOGIN_OTP.value,
        destination=user.email,
    )

    # 8. Store verification record
    verification = Verification(
        user_id=user.id,
        type=VerificationType.LOGIN_OTP,
        destination=user.email,
        code_hash=otp_hash,
        status=VerificationStatus.PENDING,
        attempts=0,
        max_attempts=5,
        expires_at=(
            datetime.now(timezone.utc)
            + timedelta(
                seconds=OTP_EXPIRE_SECONDS
            )
        ),
    )

    db.add(verification)

    await db.commit()

    
    return LoginResponse(
        message="Login verification code sent",
        otp_required=True,
    )




async def verify_login_otp_identity_service(
    db: AsyncSession,
    data: LoginVerifyRequest,
) -> LoginVerifyResponse:

    """
    Verify a user's login OTP and create an authenticated session.

    The function retrieves the latest pending login verification,
    validates its expiration and attempt limit, verifies the submitted
    OTP, marks the verification as completed, creates a new session,
    and generates access and refresh tokens.

    Args:
        db: Asynchronous SQLAlchemy database session.
        data: Login verification data containing the user's email
            and six-digit OTP.

    Returns:
        LoginVerifyResponse: Contains the generated access token,
        refresh token, token type, and access-token expiration time.

    Raises:
        HTTPException: 401 Unauthorized when the user or verification
            request is invalid.
        HTTPException: 400 Bad Request when no pending verification
            exists, the OTP has expired, the maximum number of attempts
            has been exceeded, or the OTP is invalid.
    """

    email = str(
        data.email
    ).lower().strip()

    # 1. Find user
    result = await db.execute(
        select(User).where(
            User.email == email
        )
    )

    user = result.scalar_one_or_none()

    if user is None:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid verification request",
        )

    
    result = await db.execute(
        select(Verification)
        .where(
            Verification.user_id == user.id,
            Verification.type == VerificationType.LOGIN_OTP,
            Verification.status == VerificationStatus.PENDING,
        )
        .order_by(
            Verification.created_at.desc()
        )
        .limit(1)
    )

    verification = result.scalar_one_or_none()

    if verification is None:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending login verification found",
        )

    now = datetime.now(
        timezone.utc
    )

    
    if verification.expires_at <= now:

        verification.status = (
            VerificationStatus.EXPIRED
        )

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Login verification code expired",
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
        verification_type=VerificationType.LOGIN_OTP.value,
        destination=email,
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
            detail="Invalid login verification code",
        )

    
    verification.status = (
        VerificationStatus.VERIFIED
    )

    verification.verified_at = now

   
    session = Session(
        user_id=user.id,
        status=SessionStatus.ACTIVE,
        refresh_token_hash="temporary",
        expires_at=(
            now
            + timedelta(
                days=REFRESH_TOKEN_EXPIRE_DAYS
            )
        ),
    )

    db.add(session)

    await db.flush()

  
    access_token = create_access_token(
        user_id=str(user.id),
        session_id=str(session.id),
    )

  
    refresh_token = create_refresh_token(
        user_id=str(user.id),
        session_id=str(session.id),
    )


    session.refresh_token_hash = hash_token(
        token=refresh_token
    )

    await db.commit()

    # 11. Return tokens
    expires_in = (
        ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return LoginVerifyResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=expires_in,
    )






async def refresh_access_token_identity_service(
    db: AsyncSession,
    data: RefreshTokenRequest
) -> RefreshTokenResponse:

    """
    Rotate the refresh token and generate a new access token.

    The function validates the refresh token, verifies its associated
    session and user, checks session expiration and status, validates
    the stored refresh-token hash, and rotates the refresh token.

    Args:
        db: Asynchronous SQLAlchemy database session.
        data: Request containing the current refresh token.

    Returns:
        RefreshTokenResponse: Contains a newly generated access token,
        rotated refresh token, token type, and access-token expiration
        time.

    Raises:
        HTTPException: 401 Unauthorized when the refresh token is
            invalid, malformed, expired, associated with a missing
            session, or does not match the stored token hash.
        HTTPException: 403 Forbidden when the user account is inactive.
    """

    try:
        payload=decode_token(data.refresh_token)
    except ValueError:

        raise HTTPException(
            status_code=401,
            detail="invalid refresh token"
        )

    if payload.get("type") != "refresh":

        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    user_id=payload.get("sub")
    session_id=payload.get("session_id")

    if not user_id or not session_id:
        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    result=await db.execute(
        select(Session).where(
            Session.id==session_id,
            Session.user_id==user_id
        )
    )

    session=result.scalar_one_or_none()

    if session is None:

        raise HTTPException(
            status_code=401,
            detail="Session not found"
        )

    if session.status != SessionStatus.ACTIVE:

        raise HTTPException(
            status_code=401,
            detail="Session is not active"
        )

    if session.expires_at <= datetime.now(timezone.utc):
        session.status = SessionStatus.EXPIRED


        await db.commit()


        raise HTTPException(
            status_code=401,
            detail="session expired"
        )

    result=await db.execute(
        select(User).where(
            User.id==user_id
        )
    )

    user=result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if user.status!=UserStatus.ACTIVE:

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active"
        )

    if not verify_token_hash(
        data.refresh_token,
        session.refresh_token_hash
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid refresh token"
        )

    access_token=create_access_token(
        user_id=str(user_id),
        session_id=str(session.id)
    )

    new_refresh_token=create_refresh_token(
        user_id=str(user_id),
        session_id=str(session.id)
    )

    session.refresh_token_hash = hash_token(
        new_refresh_token
    )

    await db.commit()

    expires_in=ACCESS_TOKEN_EXPIRE_MINUTES*60

    return RefreshTokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=expires_in
    )






async def logout_user_in_identity_service(
    db:AsyncSession,
    token:str
) -> None:

    """
    Revoke the authenticated user's current session.

    The function validates the access token, retrieves the associated
    session, and marks the session as revoked. If the session has
    already been revoked, the operation is treated as idempotent.

    Args:
        db: Asynchronous SQLAlchemy database session.
        token: Access token used to identify the authenticated session.

    Returns:
        None: The user's session is revoked successfully.

    Raises:
        HTTPException: 401 Unauthorized when the access token is
            invalid, has the wrong token type, or the associated
            session cannot be found.
    """

    try:
        payload=decode_token(token=token)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invblid access token"
        )

    if payload.get("type") != "access":

        raise HTTPException(
            status_code=401,
            detail="Invalid access token"
        )

    user_id=payload.get("sub")
    session_id=payload.get("session_id")

    if not user_id or not session_id:

        raise HTTPException(
            status_code=401,
            detail="Invalid access token"
        )

    result=await db.execute(
        select(Session).where(
            Session.id==session_id,
            Session.user_id==user_id
        )
    )

    session=result.scalar_one_or_none()

    if session is None:

        raise HTTPException(
            status_code=401,
            detail="session not found"
        )

    if session.status==SessionStatus.REVOKED:
        return

    session.status = SessionStatus.REVOKED
    session.revoked_at = datetime.now(
        timezone.utc
    )   

    await db.commit()

    


    