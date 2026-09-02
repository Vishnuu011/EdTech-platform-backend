from collections.abc import Callable

from fastapi import Depends, HTTPException, status

from src.domain.enums import UserRole
from src.middleware.auth.dependencies import get_current_user
from src.models.user import User


def require_role(
    *allowed_roles:UserRole,
) -> Callable:

    """
    Create a dependency that restricts access to specific user roles.

    The returned dependency checks the authenticated user's role
    against the roles provided to this function.

    Example:
        @router.get("/admin")
        async def admin_endpoint(
            current_user: User = Depends(
                require_role(UserRole.ADMIN)
            )
        ):
            ...

    Args:
        *allowed_roles: One or more roles permitted to access
            the protected endpoint.

    Returns:
        Callable: A FastAPI dependency that validates the user's role.
    """

    async def role_checker(
        current_user:User=Depends(
            get_current_user
        )
    ) -> User:

        """
        Verify that the authenticated user has an allowed role.

        Args:
            current_user: Authenticated user obtained from the
                authentication dependency.

        Returns:
            User: The authenticated user when their role is authorized.

        Raises:
            HTTPException: 403 Forbidden when the user's role is not
                included in the allowed roles.
        """

        if current_user.role not in allowed_roles:

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permission"
            )

        return current_user

    return role_checker