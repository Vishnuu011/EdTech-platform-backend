from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from src.domain.enums import UserRole
from src.middleware.auth.depecdencies import get_current_user
from src.models.user import User


def require_role(
    *allowed_roles:UserRole,
) -> Callable:

    async def role_checker(
        current_user:User=Depends(
            get_current_user
        )
    ) -> User:

        if current_user.role not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission"
            )

        return current_user

    return role_checker