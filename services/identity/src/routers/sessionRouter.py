from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from services.identity.src.middleware.auth.dependencies import get_current_user
from src.models.user import User

from src.controller.sessionController import get_user_sessions, revoke_all_user_sessions, revoke_user_session


router = APIRouter()



@router.get("")
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sessions = await get_user_sessions(
        db=db,
        user=current_user,
    )

    return [
        {
            "session_id": str(session.id),
            "status": session.status,
            "expires_at": session.expires_at,
            "created_at": session.created_at,
            "revoked_at": session.revoked_at,
        }
        for session in sessions
    ]


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_200_OK
)
async def revoke_session(
    session_id:str,
    current_user:User=Depends(
        get_current_user
    ),
    db:AsyncSession=Depends(
        get_db
    )
):

    await revoke_user_session(
        db=db,
        user=current_user,
        session_id=session_id
    )

    return {
        "message":"Session revoked successfully"
    }



@router.post(
    "/revoke-all",
    status_code=status.HTTP_200_OK
)
async def revoke_all_sessions(
    current_user:User=Depends(
        get_current_user
    ),
    db:AsyncSession=Depends(
        get_db
    )
):

    await revoke_all_user_sessions(
        db=db,
        user=current_user
    )

    return {
        "message":"All session revoked successfullly"
    }