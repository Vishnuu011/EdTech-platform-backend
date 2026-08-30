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

    """
    Create a signed JWT access token for an authenticated session.

    The access token contains the user ID, session ID, token type,
    issued-at timestamp, and expiration timestamp. Access tokens
    are short-lived and are intended to authenticate API requests.

    Args:
        user_id: Unique identifier of the authenticated user.
        session_id: Unique identifier of the user's active session.

    Returns:
        str: Signed JWT access token.

    Raises:
        Exception: If the JWT cannot be encoded using the configured
            secret and algorithm.
    """

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

    """
    Create a signed JWT refresh token for an authenticated session.

    The refresh token contains the user ID, session ID, token type,
    issued-at timestamp, and expiration timestamp. Refresh tokens
    have a longer lifetime than access tokens and are used to obtain
    new access tokens.

    Args:
        user_id: Unique identifier of the authenticated user.
        session_id: Unique identifier of the user's active session.

    Returns:
        str: Signed JWT refresh token.

    Raises:
        Exception: If the JWT cannot be encoded using the configured
            secret and algorithm.
    """

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

    """
    Decode and validate a signed JWT.

    Validates the token signature, configured signing algorithm,
    and standard JWT claims such as expiration. The decoded claims
    are returned when validation succeeds.

    Args:
        token: Encoded JWT to decode and validate.

    Returns:
        dict[str, Any]: Decoded JWT claims.

    Raises:
        ValueError: If the token is invalid, expired, malformed,
            or fails JWT validation.
    """

    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError as exc:
        raise ValueError("Invalid token") from exc