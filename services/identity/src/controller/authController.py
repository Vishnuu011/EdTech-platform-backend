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

from src.domain.enums import CredentialStatus, UserStatus, SessionStatus, SessionStatus
from src.helpers.password import hash_password
from src.models.credential import Credential
from src.models.user import User
from src.models.session import Session

from src.helpers.jwt import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    create_access_token,
    create_refresh_token,
    decode_token
)

from src.helpers.token import hash_token, verify_token_hash
from src.helpers.password import verify_password
from src.models.session import Session



class RegisterRequest(BaseModel):

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

    user_id:str
    email:EmailStr
    status:UserStatus


class LoginRequest(BaseModel):

    email: EmailStr
    password:str=Field(
        min_length=8, 
        max_length=128
    )

    

class LoginResponse(BaseModel):

    access_token:str
    refresh_token:str
    token_type:str
    expries_in:int    




class RefreshTokenRequest(BaseModel):
    refresh_token: str



class RefreshTokenResponse(BaseModel):

    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int    





async def register_identity_services_user(
    db: AsyncSession,
    data: RegisterRequest    
) -> RegisterResponse:

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
    data: LoginRequest
) -> LoginResponse:

    email=str(data.email).lower().strip()

    result=await db.execute(
        select(User).where(
            User.email==email
        )
    )

    user=result.scalar_one_or_none()

    unauth=status.HTTP_401_UNAUTHORIZED
    detail="Invalid email or password"

    if user is None:

        raise HTTPException(
            status_code=unauth,
            detail=detail
        )
    
    detail2="user account is not active"

    if user.status != UserStatus.ACTIVE:

        raise HTTPException(
            status_code=403,
            detail=detail2
        )

    result=await db.execute(
        select(Credential).where(
            Credential.user_id==user.id
        )
    )

    credential=result.scalar_one_or_none()

    
    if credential is None:
    
        raise HTTPException(
            status_code=unauth,
            detail=detail
        )
        
    detail3="Credential is not active"
    
    if credential.status != CredentialStatus.ACTIVE:
    
        raise HTTPException(
            status_code=403,
            detail=detail3
        )


    if not verify_password(
        data.password,
        credential.password_hash
    ):

        raise HTTPException(
            status_code=401,
            detail=detail
        )

    session=Session(
        user_id=user.id,
        status=SessionStatus.ACTIVE,
        refresh_token_hash="temporary",
        expires_at=datetime.now(
            timezone.utc
        ) + timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        )
    )

    db.add(session)

    await db.flush()

    access_token=create_access_token(
        user_id=str(user.id),
        session_id=str(session.id)
    )

    refresh_token=create_refresh_token(
        user_id=str(user.id),
        session_id=str(session.id)
    )

    session.refresh_token_hash=hash_token(
        token=refresh_token
    )

    await db.commit()

    expries_in=ACCESS_TOKEN_EXPIRE_MINUTES*60

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expries_in=expries_in
    )






async def refresh_access_token_identity_service(
    db: AsyncSession,
    data: RefreshTokenRequest
) -> RefreshTokenResponse:

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

    


    