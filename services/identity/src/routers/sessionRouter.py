from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from services.identity.src.middleware.auth.dependencies import get_current_user
from src.models.user import User

from src.controller.sessionController import (
    get_user_sessions, 
    revoke_all_user_sessions, 
    revoke_user_session,
    revoke_other_user_sessions
)





router = APIRouter()






@router.get("")
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    """
    Retrieve all sessions belonging to the authenticated user.

    Returns session metadata including the session ID, status,
    creation time, expiration time, and revocation time.

    Args:
        current_user: Authenticated user obtained from the access token.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        list[dict]: List of the authenticated user's sessions.

    Raises:
        HTTPException: 401 Unauthorized if the authentication token
            is invalid or the user cannot be authenticated.
    """


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


    """
    Revoke a specific session belonging to the authenticated user.

    The session ID is validated against the authenticated user's ID,
    preventing users from revoking sessions belonging to another user.

    Args:
        session_id: ID of the session to revoke.
        current_user: Authenticated user obtained from the access token.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        dict: Confirmation message indicating that the session
        was revoked successfully.

    Raises:
        HTTPException: 401 Unauthorized if the user is not authenticated.
        HTTPException: 404 Not Found if the session does not exist
            or does not belong to the authenticated user.
    """


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


    """
    Revoke all active sessions belonging to the authenticated user.

    This operation logs the user out from all currently active
    devices and sessions.

    Args:
        current_user: Authenticated user obtained from the access token.
        db: Asynchronous SQLAlchemy database session.

    Returns:
        dict: Confirmation message indicating that all active
        sessions were revoked.

    Raises:
        HTTPException: 401 Unauthorized if the user is not authenticated.
    """


    await revoke_all_user_sessions(
        db=db,
        user=current_user
    )

    return {
        "message":"All session revoked successfullly"
    }



