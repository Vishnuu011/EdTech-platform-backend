from datetime import datetime, timedelta, timezone
from typing import Any
from jose import jwt, JWTError
from src.config.settings import settings


ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=30


def create_access_token(
    user_id:str,
    session_id:str
) -> str:

    now=datetime.now(
        timezone.utc
    )

    payload:dict[str, Any]={
        "sub": user_id,
        "session_id":session_id,
        "type": "access",
        "iat": now,
        "exp": now+timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


def create_refresh_token(
    user_id:str,
    session_id:str
) -> str:

    now=datetime.now(
        timezone.utc
    )

    payload:dict[str, Any]={
        "sub": user_id,
        "session_id":session_id,
        "type": "refresh",
        "iat": now,
        "exp": now+timedelta(
            days=REFRESH_TOKEN_EXPIRE_DAYS
        )
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )


def decode_token(token: str) -> dict[str, Any]:

    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as exc:
        raise ValueError("Invalid token") from exc