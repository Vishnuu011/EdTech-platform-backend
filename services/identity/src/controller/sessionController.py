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