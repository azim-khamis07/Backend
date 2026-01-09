"""User management router endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.router import get_current_user_id
from app.modules.users.repo import UserRepository
from app.modules.users.schemas import (
    PasswordChange,
    PasswordChangeResponse,
    UserResponse,
    UserUpdate,
)
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(db: Session = Depends(get_db)) -> UserService:
    """Dependency to get user service."""
    repo = UserRepository(db)
    return UserService(repo)


@router.get("/me", response_model=UserResponse)
async def get_me(
    user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Get current user profile.

    Returns:
        Current user data
    """
    user_data = service.get_user(user_id)
    return UserResponse(**user_data)


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """
    Update current user profile.

    Returns:
        Updated user data
    """
    user_data = service.update_profile(user_id, email=data.email)
    return UserResponse(**user_data)


@router.post("/me/password", response_model=PasswordChangeResponse)
async def change_password(
    data: PasswordChange,
    user_id: int = Depends(get_current_user_id),
    service: UserService = Depends(get_user_service),
) -> PasswordChangeResponse:
    """
    Change current user password.

    Returns:
        Success message
    """
    result = service.change_password(
        user_id=user_id,
        current_password=data.current_password,
        new_password=data.new_password,
    )
    return PasswordChangeResponse(**result)
