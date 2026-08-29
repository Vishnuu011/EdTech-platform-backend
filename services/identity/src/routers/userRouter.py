from fastapi import APIRouter, Depends, status
from src.middleware.auth.depecdencies import get_current_user
from src.models.user import User


router=APIRouter()


@router.get(
    "/me",
    status_code=status.HTTP_200_OK
)
async def get_me(
    current_user:User=Depends(
        get_current_user
    )
):

    return {
        "user_id":str(current_user.id),
        "email":current_user.email,
        "display_name":current_user.display_name,
        "status":current_user.status
    }