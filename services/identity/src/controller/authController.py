from datetime import datetime, timezone

from fastapi import HTTPException, status
from pydantic import (
    BaseModel,
    EmailStr,
    Field
)
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import CredentialStatus, UserStatus
from src.helpers.password import hash_password
from src.models.credential import Credential
from src.models.user import User


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


class RegisterResponse(BaseModel):

    user_id:str
    email:EmailStr
    status:UserStatus



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

    