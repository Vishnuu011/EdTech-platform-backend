from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import SessionStatus
from src.models.session import Session
from src.models.user import User





async def get_user_sessions(
    db:AsyncSession,
    user:User
) -> list[Session]:

    """
    Retrieve all sessions belonging to a user.

    Sessions are returned in descending order by creation time,
    with the most recently created session appearing first.

    Args:
        db: Asynchronous SQLAlchemy database session.
        user: User whose sessions should be retrieved.

    Returns:
        list[Session]: List of sessions associated with the user.
    """

    result=await db.execute(
        select(
            Session
        ).where(
            Session.user_id==user.id
        )
        .order_by(
            Session.created_at.desc()
        )
    )

    return list(
        result.scalars().all()
    )






async def revoke_user_session(
    db:AsyncSession,
    user:User,
    session_id:str,
) -> None:

    """
    Revoke a specific user session.

    The function verifies that the requested session belongs to the
    specified user and marks the session as revoked. If the session
    has already been revoked, the operation is treated as idempotent.

    Args:
        db: Asynchronous SQLAlchemy database session.
        user: User who owns the session.
        session_id: Unique identifier of the session to revoke.

    Returns:
        None: The session is revoked successfully.

    Raises:
        HTTPException: 404 Not Found if the session does not exist
            or does not belong to the specified user.
    """

    result=await db.execute(
        select(Session).where(
            Session.id==session_id,
            Session.user_id==user.id,
        )
    )

    session=result.scalar_one_or_none()

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    if session.status==SessionStatus.REVOKED:
        return

    session.status=SessionStatus.REVOKED
    session.revoked_at=datetime.now(
        timezone.utc
    )

    await db.commit()




async def revoke_all_user_sessions(
    db:AsyncSession,
    user:User,
) -> None:

    """
    Revoke all active sessions belonging to a user.

    The function retrieves all active sessions for the specified user
    and marks each session as revoked using the same revocation
    timestamp.

    Args:
        db: Asynchronous SQLAlchemy database session.
        user: User whose active sessions should be revoked.

    Returns:
        None: All active sessions belonging to the user are revoked.
    """

    result = await db.execute(
        select(Session).where(
            Session.user_id==user.id,
            Session.status==SessionStatus.ACTIVE,
        )
    )

    sessions = result.scalars().all()

    now = datetime.now(timezone.utc)

    for session in sessions:
        session.status=SessionStatus.REVOKED
        session.revoked_at=now

    await db.commit()



async def revoke_other_user_sessions(
    db: AsyncSession,
    user: User,
    current_session_id: str,
) -> None:
    """
    Revoke all active sessions belonging to a user except the current session.

    This is useful for security features such as "Log out all other
    devices", where the user's current session should remain active
    while all other active sessions are invalidated.

    Args:
        db: Asynchronous SQLAlchemy database session.
        user: User whose other sessions should be revoked.
        current_session_id: Unique identifier of the session that
            should remain active.

    Returns:
        None: All other active sessions are revoked.
    """

    result = await db.execute(
        select(Session).where(
            Session.user_id == user.id,
            Session.status == SessionStatus.ACTIVE,
            Session.id != current_session_id,
        )
    )

    sessions = result.scalars().all()

    now = datetime.now(timezone.utc)

    for session in sessions:
        session.status = SessionStatus.REVOKED
        session.revoked_at = now

    await db.commit()    