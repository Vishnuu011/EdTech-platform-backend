from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.controller.authController import(
    RegisterResponse, 
    RegisterRequest,
    register_identity_services_user
)

from src.database.session import get_db


router=APIRouter()


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED
)
async def register_user(
    data: RegisterRequest,
    db: AsyncSession=Depends(
        get_db
    )
) -> RegisterResponse:

    return await register_identity_services_user(
        data=data,
        db=db
    )