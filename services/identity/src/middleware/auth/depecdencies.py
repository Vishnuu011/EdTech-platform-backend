from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.domain.enums import SessionStatus, UserStatus
from src.helpers.jwt import decode_token
from src.models.session import Session
from src.models.user import User


oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login"
)





async def get_current_user(
    token:str=Depends(
        oauth2_scheme
    ),
    db:AsyncSession=Depends(
        get_db
    ),
) -> User:

    # 1. Decode access token
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # 2. Make sure this is an access token
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # 3. Extract user and session IDs
    user_id = payload.get("sub")
    session_id = payload.get("session_id")

    if not user_id or not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # 4. Find session
    result = await db.execute(
        select(Session).where(
            Session.id == session_id,
            Session.user_id == user_id,
        )
    )

    session = result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # 5. Session must be active
    if session.status != SessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session is not active",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # 6. Find user
    result = await db.execute(
        select(User).where(
            User.id == user_id
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={
                "WWW-Authenticate": "Bearer"
            },
        )

    # 7. User must be active
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is not active",
        )

    return user

