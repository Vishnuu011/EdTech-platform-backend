from fastapi import APIRouter, Depends, status
from src.middleware.auth.dependencies import get_current_user

from src.models.user import User



router=APIRouter()


@router.get("/me", status_code=status.HTTP_200_OK)
async def get_me(
    current_user:User=Depends(
        get_current_user
    )
):

    """
    Retrieve the profile of the currently authenticated user.

    The authenticated user is resolved from the access token using
    the authentication dependency.

    Args:
        current_user: Authenticated user obtained from the access token.

    Returns:
        dict: Basic profile information including the user's ID,
        email, display name, account status, and role.

    Raises:
        HTTPException: 401 Unauthorized if the access token is
            missing, invalid, expired, or the user cannot be found.
    """


    return {
        "user_id":str(current_user.id),
        "email":current_user.email,
        "display_name":current_user.display_name,
        "status":current_user.status,
        "role":current_user.role
    }

 
